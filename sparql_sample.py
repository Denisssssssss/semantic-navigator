from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://lobachevskii-dml.ru:8890/sparql")
queryString = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?label
    WHERE { <http://dbpedia.org/resource/Asturias> rdfs:label ?label }
"""
sparql.setQuery(queryString)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# print(results, "\n")

if (len(results["results"]["bindings"]) == 0):
    print("No results found.")
else:
    for result in results["results"]["bindings"]:
        print(result["label"]["value"])

class OntoMathPro:

    sparql = SPARQLWrapper("http://lobachevskii-dml.ru:8890/sparql")

    def query(self):
