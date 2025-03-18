from elasticsearch import Elasticsearch

# Connect to the Elasticsearch instance
es = Elasticsearch(["http://localhost:19200"])

# Define the index and document ID
index_name = "castor-test-enron"
document_id = "test_dade1ab3a86343ed2a61f2e3d6413cbd"  # Replace with the actual document ID

query = {
    "query": {
        "match_all": {}
    },
    "size": 3000
}

# Perform the search
#response = es.search(index=index_name, body=query)

#print(len(response['hits']['hits']))

#for hit in response['hits']['hits']:
#    print(hit["_source"])

# Get the document by ID
# http://localhost:19200/castor-test-enron/_doc/test_dade1ab3a86343ed2a61f2e3d6413cbd?pretty
response = es.get(index=index_name, id=document_id)
#Print the document
print(response["_source"])
