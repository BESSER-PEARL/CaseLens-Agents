import json

from besser.agent.nlp.llm.llm import LLM
from besser.agent.nlp.llm.llm_openai_api import LLMOpenAI
from pydantic import BaseModel
from besser.agent.core.session import Session

from app.vars import *


def build_query(date_from=None, date_to=None, filters=None):
    query = {"query": {"bool": {"filter": []}}}
    # Add date range filter if parameters are provided
    if date_from or date_to:
        date_range = {}
        if date_from:
            date_range["gte"] = date_from
        if date_to:
            date_range["lte"] = date_to

        query["query"]["bool"]["filter"].append({"range": {DATE_CREATED: date_range}})

    # Add filters
    if filters:
        for f in filters:
            field, operator, value = f[FIELD], f[OPERATOR], f[VALUE]
            # if operator == "equals":
            #     query["query"]["bool"]["filter"].append({"term": {field: value}}) # This only for fields keyword fields
            # elif operator == "different":
            #     query["query"]["bool"].setdefault("must_not", []).append({"term": {field: value}})
            if operator == EQUALS:
                query["query"]["bool"]["filter"].append({"match_phrase": {field: value}})  # This only for fields with analyzed text (SUBJECT, CONTENT)
            elif operator == DIFFERENT:
                query["query"]["bool"].setdefault("must_not", []).append({"match_phrase": {field: value}})
            elif operator == CONTAINS:
                query["query"]["bool"]["filter"].append({"wildcard": {field: f"*{value}*"}})
            elif operator == STARTS_WITH:
                query["query"]["bool"]["filter"].append({"prefix": {field: value}})
            elif operator == REGEXP:
                query["query"]["bool"]["filter"].append({"regexp": {field: value}})
            elif operator == FUZZY:
                query["query"]["bool"]["filter"].append({"fuzzy": {field: {"value": value, "fuzziness": "AUTO"}}})
    return query


def get_num_docs(es_client, index_name, query):
    # Perform the count query by using size=0 to avoid retrieving documents
    response = es_client.search(index=index_name, body=query, size=0, track_total_hits=True)
    total_hits = response["hits"]["total"]["value"]
    return total_hits


def scroll_docs(session: Session, es_client, index_name, query, request, llm: LLM, scroll_time="1m", batch_size=100):
    # Start the scroll
    response = es_client.search(index=index_name, body=query, scroll=scroll_time, size=batch_size)
    # Extract the scroll ID and process the first batch
    scroll_id = response['_scroll_id']
    total_docs = response["hits"]["total"]["value"]
    updated_docs = 0
    ignored_docs = 0
    fields = set()
    prompt_filters = 'Filters:\n'
    for i, instruction in enumerate(request[INSTRUCTIONS]):
        prompt_filters += f"{i+1}: {instruction[TEXT]}"
        if instruction[FIELD]:
            prompt_filters += f"(\"{instruction[FIELD]}\" field)"
            fields.add(instruction[FIELD])
        prompt_filters += "\n"
    ids = []
    # Process the documents in batches
    while len(response["hits"]["hits"]) > 0:
        # Process each document in the current batch
        # print(f'Total scroll size: {len(response["hits"]["hits"])}')
        for doc in response["hits"]["hits"]:
            doc_not_labeled = True
            if (request[ACTION] == DOCUMENT_RELEVANCE and DOCUMENT_RELEVANCE in doc['_source'] and doc['_source'][DOCUMENT_RELEVANCE] == request[TARGET_VALUE]) \
                    or (request[ACTION] == DOCUMENT_LABELS and DOCUMENT_LABELS in doc['_source'] and doc['_source'][DOCUMENT_LABELS] is not None and request[TARGET_VALUE] in doc['_source'][DOCUMENT_LABELS]):
                # Doc already has the target score/label
                doc_not_labeled = False
            if doc_not_labeled:
                #print(doc["_source"])  # Example: print the document content
                if fields:
                    prompt_doc = {
                        field: doc['_source'][field] for field in fields
                    }
                else:
                    prompt_doc = {
                        SUBJECT: doc['_source'][SUBJECT],
                        CONTENT: doc['_source'][CONTENT],
                        FROM: doc['_source'][FROM],
                        TO: doc['_source'][TO],
                    }
                prompt = prompt_filters + f"Document:\n{prompt_doc}"
                llm_prediction = run_llm_openai(llm, prompt) if isinstance(llm, LLMOpenAI) else run_llm(llm, prompt)
                if llm_prediction:
                    updated_docs += 1
                    ids.append(doc['_id'])  # TODO: To show list of updated docs
                    if request[ACTION] == DOCUMENT_RELEVANCE:
                        update_document_relevance_id(
                            es_client=es_client,
                            index_name=index_name,
                            doc_id=doc['_id'],
                            relevance_value=request[TARGET_VALUE]
                        )
                    elif request[ACTION] == DOCUMENT_LABELS:
                        append_document_label_id(
                            es_client=es_client,
                            index_name=index_name,
                            doc_id=doc['_id'],
                            new_label=request[TARGET_VALUE]
                        )
                else:
                    ignored_docs += 1
            else:
                updated_docs += 1
            session.reply(json.dumps({REQUEST_ID: session.get(REQUEST)[REQUEST_ID], UPDATED_DOCS: updated_docs, IGNORED_DOCS: ignored_docs, TOTAL_DOCS: total_docs, FINISHED: False}))
        # Get the next batch using the scroll ID
        response = es_client.scroll(scroll_id=scroll_id, scroll=scroll_time)

    # Clear the scroll context when done
    es_client.clear_scroll(scroll_id=scroll_id)
    session.reply(json.dumps({REQUEST_ID: session.get(REQUEST)[REQUEST_ID], UPDATED_DOCS: updated_docs, IGNORED_DOCS: ignored_docs, TOTAL_DOCS: total_docs, FINISHED: True}))


def append_document_label_query(es_client, index_name, query, new_label):
    """
    Updates the DOCUMENT_LABELS field in Elasticsearch by adding a new value to the list using update_by_query.

    :param es_client: Elasticsearch client instance
    :param index_name: Name of the Elasticsearch index
    :param query: Query to find matching documents
    :param new_label: Label to add to the DOCUMENT_LABELS field
    :return: Elasticsearch response
    """
    update_body = {
        "script": {
            "source": f"""
                if (ctx._source.{DOCUMENT_LABELS} == null) {{
                    ctx._source.{DOCUMENT_LABELS} = [params.new_label];
                }} else if (!ctx._source.{DOCUMENT_LABELS}.contains(params.new_label)) {{
                    ctx._source.{DOCUMENT_LABELS}.add(params.new_label);
                }}
            """,
            "params": {
                "new_label": new_label
            }
        },
        "query": query["query"]  # Use the same query to match documents
    }

    # Perform the update_by_query to update all matching documents
    response = es_client.update_by_query(index=index_name, body=update_body)
    # print(f"Documents updated: {response['updated']}")
    return response


def append_document_label_id(es_client, index_name, doc_id, new_label):
    """
    Appends a new label to the DOCUMENT_LABELS list of a document by its ID.

    :param es_client: Elasticsearch client instance
    :param index_name: Name of the Elasticsearch index
    :param doc_id: ID of the document to update
    :param new_label: Label to add to DOCUMENT_LABELS
    :return: Elasticsearch response
    """
    update_body = {
        "script": {
            "source": f"""
                if (ctx._source.{DOCUMENT_LABELS} == null) {{
                    ctx._source.{DOCUMENT_LABELS} = [params.new_label];
                }} else if (!ctx._source.{DOCUMENT_LABELS}.contains(params.new_label)) {{
                    ctx._source.{DOCUMENT_LABELS}.add(params.new_label);
                }}
            """,
            "params": {
                "new_label": new_label
            }
        }
    }

    response = es_client.update(index=index_name, id=doc_id, body=update_body)

    # print(f"Label '{new_label}' appended to document {doc_id}.")
    return response


def update_document_relevance_id(es_client, index_name, doc_id, relevance_value):
    """
    Updates the DOCUMENT_RELEVANCE field for a document by its ID.

    :param es_client: Elasticsearch client instance
    :param index_name: Name of the Elasticsearch index
    :param doc_id: ID of the document to update
    :param relevance_value: New integer value for DOCUMENT_RELEVANCE
    :return: Elasticsearch response
    """
    update_body = {
        "doc": {
            DOCUMENT_RELEVANCE: relevance_value
        }
    }

    response = es_client.update(index=index_name, id=doc_id, body=update_body)

    # print(f"DOCUMENT_RELEVANCE updated to {relevance_value} for document {doc_id}.")
    return response


def update_document_relevance_query(es_client, index_name, query, document_relevance):
    # Prepare the update query
    update_body = {
        "script": {
            "source": f"ctx._source.{DOCUMENT_RELEVANCE} = params.relevance_value",
            "params": {
                "relevance_value": document_relevance
            }
        },
        "query": query["query"]  # Use the same query to match documents
    }
    # Perform the update_by_query to update the DOCUMENT_RELEVANCE field
    response = es_client.update_by_query(index=index_name, body=update_body)

    #print(f"Documents updated: {response['updated']}")
    return response


def run_llm_openai(llm: LLMOpenAI, prompt: str) -> bool:
    class LLMOutput(BaseModel):
        result: bool

    instruction = "Your task is to filter documents from an elasticsearch index based on some natural language conditions. You will receive a list of filters, which may relate to a specific document field, and an elasticsearch document. Return True if the document satisfies all the filters, and False otherwise.\n"
    answer = llm.client.beta.chat.completions.parse(
        model=llm.name,
        messages=[
            {"role": "user", "content": instruction + prompt}
        ],
        response_format=LLMOutput
    )
    return answer.choices[0].message.parsed.result


def run_llm(llm: LLM, prompt: str) -> bool:
    instruction = "Your task is to filter documents from an elasticsearch index based on some natural language conditions. You will receive a list of filters, which may relate to a specific document field, and an elasticsearch document. Return a JSON with this structure: {'result': True} if the document satisfies all the filters, and {'result': False} otherwise.\nFilters:\n"
    answer = llm.predict(instruction + prompt)
    if 'true' in answer.lower():
        return True
    return False
