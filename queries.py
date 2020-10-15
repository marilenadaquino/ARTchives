# -*- coding: utf-8 -*-
import conf , os , operator , pprint , ssl , rdflib
from SPARQLWrapper import SPARQLWrapper, JSON
from collections import defaultdict
from rdflib import URIRef , XSD, Namespace , Literal
from rdflib.namespace import OWL, DC , DCTERMS, RDF , RDFS
from rdflib.plugins.sparql import prepareQuery
from pymantic import sparql

ssl._create_default_https_context = ssl._create_unverified_context
server = sparql.SPARQLServer(conf.artchivesEndpoint)
dir_path = os.path.dirname(os.path.realpath(__file__))

pp = pprint.PrettyPrinter(indent=1)

queryRecords = """
	PREFIX prov: <http://www.w3.org/ns/prov#>
	PREFIX art: <https://w3id.org/artchives/>
	SELECT DISTINCT ?g ?nameHistorian ?userLabel ?modifierLabel ?date ?stage
	WHERE
	{ GRAPH ?g {
	    ?s ?p ?o .
		OPTIONAL {?g rdfs:label ?nameHistorian; prov:wasGeneratedBy ?user; prov:generatedAtTime ?date ; art:publicationStage ?stage. ?user rdfs:label ?userLabel .
			OPTIONAL {?g prov:wasInfluencedBy ?modifier. ?modifier rdfs:label ?modifierLabel .} }
		OPTIONAL {?g rdfs:label ?nameHistorian; prov:generatedAtTime ?date ; art:publicationStage ?stage . }
		FILTER( str(?g) != "https://w3id.org/artchives/wd/")
		BIND(COALESCE(?date, '-') AS ?date ).
		BIND(COALESCE(?stage, '-') AS ?stage ).
		BIND(COALESCE(?userLabel, '-') AS ?userLabel ).
		BIND(COALESCE(?modifierLabel, '-') AS ?modifierLabel ).
		BIND(COALESCE(?nameHistorian, 'none', '-') AS ?nameHistorian ).
		filter not exists {
	      ?g prov:generatedAtTime ?date2
	      filter (?date2 > ?date)

	    }
	  }
	}
	"""

queryHistorians = """
	PREFIX wd: <http://www.wikidata.org/entity/>
	PREFIX wdp: <http://www.wikidata.org/wiki/Property:>
	SELECT DISTINCT ?artHistorian ?nameHistorian ?image
	WHERE
	{ GRAPH ?g {
		?artHistorian a wd:Q5 ; rdfs:label ?nameHistorian .
		?coll wdp:P170 ?artHistorian .
		OPTIONAL {?artHistorian wdp:P18 ?image .}
	  }
	}
	"""

queryCollections = """
	PREFIX prov: <http://www.w3.org/ns/prov#>
	PREFIX art: <https://w3id.org/artchives/>
	PREFIX wdp: <http://www.wikidata.org/wiki/Property:>
	SELECT *
	WHERE
	{ GRAPH ?g {
		?g rdfs:label ?nameHistorian; art:publicationStage ?stage .
		?coll wdp:P170 ?artHistorian ; rdfs:label ?nameCollection .
		OPTIONAL {?artHistorian wdp:P18 ?image .}
	  }
	}
	"""

queryCollectionsByPeriod = """
	PREFIX prov: <http://www.w3.org/ns/prov#>
	PREFIX art: <https://w3id.org/artchives/>
	PREFIX wdp: <http://www.wikidata.org/wiki/Property:>
	SELECT DISTINCT *
	WHERE
	{ GRAPH ?g {
		?g rdfs:label ?nameHistorian; art:publicationStage ?stage .
		?coll wdp:P170 ?artHistorian ; rdfs:label ?nameCollection .
		OPTIONAL {?coll art:hasSubjectPeriod ?period . ?period rdfs:label ?periodLabel . }
		OPTIONAL {?coll art:hasNotesOnScopeAndContent ?scope. BIND( SUBSTR(?scope, 1, 150) AS ?abstract ) .}
	  }

	  OPTIONAL {?period <http://www.wikidata.org/prop/direct/P582> ?end_date } .
	  OPTIONAL {?period <http://www.wikidata.org/prop/direct/P580> ?start_date } .
	  OPTIONAL {?period art:wikidataReconciliation ?wd_stage } .
	}
	"""

queryKeepers = """
	PREFIX wd: <http://www.wikidata.org/entity/>
	SELECT DISTINCT ?keeper ?nameKeeper
	WHERE
	{ GRAPH ?g {
		?keeper a wd:Q31855 ; rdfs:label ?nameKeeper .
	  }
	}
	"""



queryBiblio = """
	PREFIX wd: <http://www.wikidata.org/entity/>
	PREFIX wdp: <http://www.wikidata.org/wiki/Property:>
	SELECT DISTINCT ?nameCollection ?otherbiblioRefLabel ?collbiblioLabel
	WHERE {
	 {GRAPH ?g{
       	?artHistorian a wd:Q5 ; rdfs:label ?nameHistorian .
		?otherbiblioRef wdp:P921 ?artHistorian ; rdfs:label ?otherbiblioRefLabel .
       ?coll wdp:P170 ?artHistorian ; rdfs:label ?nameCollection .
       BIND(COALESCE(?otherbiblioRefLabel, "") AS ?otherbiblioRefLabel).
      	optional {
      	?otherbiblioColl wdp:P921 ?coll ; rdfs:label ?collbiblioLabel .

		}
		BIND(COALESCE(?collbiblioLabel, "") AS ?collbiblioLabel).

	  }
     }
}
	"""




def getRecordCreator(graph_name):
	""" get the label of the creator of a record """
	creatorIRI, creatorLabel = None, None
	queryRecordCreator = """
		PREFIX wd: <http://www.wikidata.org/entity/>
		PREFIX prov: <http://www.w3.org/ns/prov#>
		SELECT DISTINCT ?creatorIRI ?creatorLabel
		WHERE { <"""+graph_name+"""> prov:wasGeneratedBy ?creatorIRI .
		?creatorIRI rdfs:label ?creatorLabel . }"""
	#print(queryRecordCreator)
	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(queryRecordCreator)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	for result in results["results"]["bindings"]:
		creatorIRI, creatorLabel = result["creatorIRI"]["value"],result["creatorLabel"]["value"]
	return creatorIRI, creatorLabel

def getRecords():
	""" get all the records created by users to list them in the backend welcome page """
	records = set()
	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(queryRecords)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	for result in results["results"]["bindings"]:
		records.add( (result["g"]["value"], result["nameHistorian"]["value"], result["userLabel"]["value"], result["modifierLabel"]["value"], result["date"]["value"], result["stage"]["value"] ))
	return records

def getHistorians():
	""" get all the records on historians to populate the /historians page """
	records = set()
	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(queryHistorians)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	for result in results["results"]["bindings"]:
		if 'image' in result:
			records.add( ( result["artHistorian"]["value"], result["nameHistorian"]["value"].lstrip().rstrip(), result["image"]["value"] ))
		else:
			records.add( ( result["artHistorian"]["value"], result["nameHistorian"]["value"].lstrip().rstrip(), 'no image available' ))
	return records

def getCollections():
	""" get all the records on historians to populate the /collections page """
	records = set()
	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(queryCollections)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	for result in results["results"]["bindings"]:
		if 'image' in result:
			records.add( (result["g"]["value"], result["coll"]["value"], result["nameCollection"]["value"].lstrip().rstrip(), result["image"]["value"], result["stage"]["value"] ))
		else:
			records.add( (result["g"]["value"], result["coll"]["value"], result["nameCollection"]["value"].lstrip().rstrip(), 'no image available', result["stage"]["value"] ))
	return records

def getCollectionsByPeriod():
	""" get all the records on collections grouped by period to populate the /contents page """

	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(queryCollectionsByPeriod)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	records = defaultdict(dict)
	for result in results["results"]["bindings"]:
		collection_path = "collection-"+result["g"]["value"].split("artchives/",1)[1].replace('/','')
		collection_name = result["nameCollection"]["value"].strip()
		# collection w/ periods
		if 'period' in result and 'periodLabel' in result:
			period = result['period']['value']
			periodLabel = result['periodLabel']['value'].strip()
			if period not in records:
				records[period]['period_label'] = periodLabel
			if collection_path not in records[period]:

				if 'abstract' in result:
					records[period][collection_path] = [collection_name, result["abstract"]["value"].strip().replace('\n', ' ').replace('\r', '')]
				else:
					records[period][collection_path] = [collection_name, '']
				if ('start_date' in result and result['start_date']['value'] != '') or ('end_date' in result and result['end_date']['value'] != '') :
					if 'start_date' in result:
						records[period]["start_date"] = str(result['start_date']['value'])[:10][::-1].replace('-',',',2)[::-1]
					if 'end_date' in result:
						records[period]["end_date"] = str(result['end_date']['value'])[:10][::-1].replace('-',',',2)[::-1]
				else:
					if 'entity' in period:
						dates = ['no date','no date']
						if 'wd_stage' not in result:
							print("calling wikidata for:" + period)
							dates = getDatesWD(period)
						if dates[0] != 'no date':
							records[period]["start_date"] = str(dates[0])[:10][::-1].replace('-',',',2)[::-1]
						else:
							records[period]["start_date"] = '0001,01,01'
						if dates[1] != 'no date':
							records[period]["end_date"] = str(dates[1])[:10][::-1].replace('-',',',2)[::-1]
						else:
							if dates[0] == 'no date':
								records[period]["end_date"] = '2020,01,01'
					if 'artchives' in period:
						records[period]["start_date"] = '0001,01,01'
						records[period]["end_date"] = '2020,01,01'
		else: # collection without periods
			records['no_period']['period_label'] = 'Not specified'
			if collection_path not in records['no_period']:
				records['no_period'][collection_path] = collection_name
				records['no_period']["start_date"] = '2020,01,01'
				#records['no_period']["end_date"] = '2020,01,01'
			if 'abstract' in result:
				records['no_period'][collection_path] = [collection_name, result["abstract"]["value"].strip().replace('\n', ' ').replace('\r', '')]
			else:
				records['no_period'][collection_path] = [collection_name, '']

	records = dict(records)
	pp.pprint(records)
	return records


def getDatesWD(period):
	""" query wikidata to get dates of periods.
	Upload to the triplestore to store the information for fast retrieval """
	queryWdDates = """
		SELECT ?start_date ?end_date
		WHERE {

			OPTIONAL {<"""+period+"""> <http://www.wikidata.org/prop/direct/P580> ?start_date_1 } .
	  	  	OPTIONAL {<"""+period+"""> <http://www.wikidata.org/prop/direct/P571> ?start_date_2 } .
	  	  	OPTIONAL {<"""+period+"""> <http://www.wikidata.org/prop/direct/P361> ?broader_period.
	  	   			?broader_period <http://www.wikidata.org/prop/direct/P571> ?start_date_3 } .
			OPTIONAL {<"""+period+"""> <http://www.wikidata.org/prop/direct/P361> ?broader_period.
	  	   			?broader_period <http://www.wikidata.org/prop/direct/P580> ?start_date_3_1 } .
	  	  	OPTIONAL {<"""+period+"""> <http://www.wikidata.org/prop/direct/P2596> ?culture .
	  	  			?culture <http://www.wikidata.org/prop/direct/P571> ?start_date_4 } .
			OPTIONAL {<"""+period+"""> <http://www.wikidata.org/prop/direct/P2348> ?culture .
	  	  			?culture <http://www.wikidata.org/prop/direct/P580> ?start_date_5 } .
	  	   	BIND(COALESCE(?start_date_1, ?start_date_2, ?start_date_3, ?start_date_3_1, ?start_date_4, ?start_date_5) AS ?start_date) .

			OPTIONAL {<"""+period+"""> <http://www.wikidata.org/prop/direct/P582> ?end_date_1} .
			OPTIONAL {<"""+period+"""> <http://www.wikidata.org/prop/direct/P2348> ?culture .
	  	  			?culture <http://www.wikidata.org/prop/direct/P582> ?end_date_2 } .
			OPTIONAL {<"""+period+"""> <http://www.wikidata.org/prop/direct/P361> ?broader_period.
	  	   			?broader_period <http://www.wikidata.org/prop/direct/P582> ?end_date_3 } .
			BIND(COALESCE(?end_date_1, ?end_date_2, ?end_date_3) AS ?end_date) .
			}
	"""
	sparqlWD = SPARQLWrapper(conf.wikidataEndpoint)
	sparqlWD.setQuery(queryWdDates)
	sparqlWD.setReturnFormat(JSON)
	resultsWD = sparqlWD.query().convert()

	base = 'https://w3id.org/artchives/'
	wd = rdflib.Graph(identifier=URIRef(base+'wd/'))
	WDP = Namespace("http://www.wikidata.org/prop/direct/")

	for resultWD in resultsWD["results"]["bindings"]:
		if "start_date" in resultWD:
			start_date = resultWD["start_date"]["value"]
			wd.add(( URIRef(period), URIRef("http://www.wikidata.org/prop/direct/P580"), Literal(start_date,datatype=XSD.dateTime)  ))
		else:
			start_date = 'no date'

		if "end_date" in resultWD:
			end_date = resultWD["end_date"]["value"]
			wd.add(( URIRef(period), URIRef("http://www.wikidata.org/prop/direct/P582"), Literal(end_date,datatype=XSD.dateTime)  ))
		else:
			end_date = 'no date'

		recordID = period.split("entity/",1)[1] if 'entity' in period else period.split("artchives/",1)[1]

		if len(wd) == 0:
			wd.add(( URIRef(period), URIRef("https://w3id.org/artchives/wikidataReconciliation"), Literal("no data added")  ))
		# Create a copy in folder /records and load on the triplestore
		wd.serialize(destination='records/'+recordID+'.ttl', format='ttl', encoding='utf-8')
		server.update('load <file:///'+dir_path+'/records/'+recordID+'.ttl> into graph <'+base+'wd/>')
	return [start_date,end_date]

def getKeepers():
	""" get all the records on historians to populate the /keepers page """
	records = set()
	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(queryKeepers)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	for result in results["results"]["bindings"]:
		records.add( (result["keeper"]["value"], result["nameKeeper"]["value"].lstrip().rstrip().replace('%u2013','-') ))
	print(records)
	return records


def getHistorian(artHistorianURI):
	""" get info about the selected historian to populate the entry"""
	queryHistorian = """
		PREFIX wd: <http://www.wikidata.org/entity/>
		PREFIX wdp: <http://www.wikidata.org/wiki/Property:>
		PREFIX dcterms: <http://purl.org/dc/terms/>
		PREFIX art: <https://w3id.org/artchives/>
		SELECT *
		WHERE {
			GRAPH ?g
			{
				<"""+artHistorianURI+"""> a wd:Q5; rdfs:label ?artHistorianLabel .
				OPTIONAL {  ?collection rdf:type wd:Q9388534 ; wdp:P170 <"""+artHistorianURI+"""> ; rdfs:label ?collectionLabel . }
				OPTIONAL {  ?collection art:hasNotesOnScopeAndContent ?scopeSubject . ?scopeSubject rdfs:label ?scopeSubjectLabel .}
				OPTIONAL {	?artHistorian wdp:P569 ?birthDate ; wdp:P570 ?deathDate . }
				OPTIONAL {	?artHistorian wdp:P106 ?role . ?role rdfs:label ?roleLabel . }
				OPTIONAL {	?artHistorian wdp:P27 ?countryCreator . ?countryCreator rdfs:label ?countryCreatorLabel . }
				OPTIONAL {	?artHistorian dcterms:description ?bio . }
				OPTIONAL {	?artHistorian wdp:P921 ?bioSubject . ?bioSubject rdfs:label ?bioSubjectLabel . }
				OPTIONAL {	?artHistorian wdp:P800 ?artBiblioRef . ?artBiblioRef rdfs:label ?artBiblioRefLabel . }
				OPTIONAL {	?otherbiblioRef wdp:P921 ?artHistorian ; rdfs:label ?otherbiblioRefLabel . }

			}

		} """
	records = set()
	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(queryHistorian)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	#print(queryHistorian)
	data = {}
	for result in results["results"]["bindings"]:
		# S_CREATOR_1
		if 'artHistorianLabel' in result:
			S_CREATOR_1 = 'S_CREATOR_1-'+artHistorianURI.rsplit('/', 1)[-1]
			data[S_CREATOR_1] = defaultdict(dict)
			data[S_CREATOR_1][artHistorianURI.rsplit('/', 1)[-1]] = result["artHistorianLabel"]["value"]

		# S_CREATOR_2
		if 'birthDate' in result and 'deathDate' in result:
			data['S_CREATOR_2'] = result["birthDate"]["value"]+'-'+result["deathDate"]["value"]
		elif 'birthDate' in result and 'deathDate' not in result:
			data['S_CREATOR_2'] = result["birthDate"]["value"]+'-'
		elif 'deathDate' in result and 'birthDate' not in result:
			data['S_CREATOR_2'] = '-'+result["deathDate"]["value"]

		# S_CREATOR_3
		if 'roleLabel' in result:
			S_CREATOR_3 = 'S_CREATOR_3-'+result["role"]["value"].rsplit('/', 1)[-1]
			data[S_CREATOR_3] = defaultdict(dict)
			data[S_CREATOR_3][result["role"]["value"].rsplit('/', 1)[-1]] = result["roleLabel"]["value"]

		# S_CREATOR_4
		if 'countryCreatorLabel' in result:
			S_CREATOR_4 = 'S_CREATOR_4-'+result["countryCreator"]["value"].rsplit('/', 1)[-1]
			data[S_CREATOR_4] = defaultdict(dict)
			data[S_CREATOR_4][result["countryCreator"]["value"].rsplit('/', 1)[-1]] = result["countryCreatorLabel"]["value"]

		# S_CREATOR_5
		if 'bio' in result:
			data['S_CREATOR_5'] = result["bio"]["value"]

		if 'bioSubjectLabel' in result:
			S_CREATOR_5 = 'S_CREATOR_5-'+result["bioSubject"]["value"].rsplit('/', 1)[-1]
			data[S_CREATOR_5] = defaultdict(dict)
			data[S_CREATOR_5][result["bioSubject"]["value"].rsplit('/', 1)[-1]] = result["bioSubjectLabel"]["value"]

		# S_CREATOR_6
		if 'artBiblioRefLabel' in result:
			data['S_CREATOR_6'] = result["artBiblioRefLabel"]["value"]
			# S_CREATOR_6 = 'S_CREATOR_6-'+result["artBiblioRef"]["value"].rsplit('/', 1)[-1]
			# data[S_CREATOR_6] = defaultdict(dict)
			# data[S_CREATOR_6][result["artBiblioRef"]["value"].rsplit('/', 1)[-1]] = result["artBiblioRefLabel"]["value"]

		# S_CREATOR_7
		if 'otherbiblioRefLabel' in result:
			data['S_CREATOR_7'] = result["otherbiblioRefLabel"]["value"]
			# S_CREATOR_7 = 'S_CREATOR_7-'+result["otherbiblioRef"]["value"].rsplit('/', 1)[-1]
			# data[S_CREATOR_7] = defaultdict(dict)
			# data[S_CREATOR_7][result["otherbiblioRef"]["value"].rsplit('/', 1)[-1]] = result["otherbiblioRefLabel"]["value"]

		# S_COLL_2
		if 'collectionLabel' in result:
			graphID = result["g"]["value"][:-1]
			S_COLL_2 = 'S_COLL_2-'+graphID.rsplit('/', 1)[-1]
			data[S_COLL_2] = defaultdict(dict)
			data[S_COLL_2][graphID.rsplit('/', 1)[-1]] = result["collectionLabel"]["value"]

		if 'scopeSubjectLabel' in result:
			S_COLL_8 = 'S_COLL_8-'+result["scopeSubject"]["value"].rsplit('/', 1)[-1]
			data[S_COLL_8] = defaultdict(dict)
			data[S_COLL_8][result["scopeSubject"]["value"].rsplit('/', 1)[-1]] = result["scopeSubjectLabel"]["value"]

	return data


def getKeeper(keeperURI):
	""" get info about the selected keeper to populate the entry"""
	queryKeeper = '''
		PREFIX wd: <http://www.wikidata.org/entity/>
		PREFIX wdp: <http://www.wikidata.org/wiki/Property:>
		PREFIX dcterms: <http://purl.org/dc/terms/>
		PREFIX art: <https://w3id.org/artchives/>
		SELECT *
		WHERE {
			GRAPH ?g
			{ 	<'''+keeperURI+'''> rdfs:label ?keeperLabel ; wdp:P1830 ?collection.
				?collection rdf:type wd:Q9388534 ; rdfs:label ?collectionLabel .
				OPTIONAL {	?keeper wdp:P969 ?address .}
				OPTIONAL {	?keeper wdp:P131 ?cityKeeper .
							?cityKeeper rdfs:label ?cityKeeperLabel .
							OPTIONAL {?cityKeeper wdp:P131 ?districtKeeper . ?districtKeeper rdfs:label ?districtKeeperLabel . }
						 }
				OPTIONAL {	?keeper wdp:P17 ?countryKeeper . ?countryKeeper rdfs:label ?countryKeeperLabel .}
				OPTIONAL {	?keeper wdp:P1329 ?phone .}
				OPTIONAL {	?keeper wdp:P968 ?email .}
				OPTIONAL {	?keeper wdp:P856 ?websiteKeeper .}

			}

		}
		'''
	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(queryKeeper)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	data = {}
	# S_KEEPER_1
	for result in results["results"]["bindings"]:
		if result["keeperLabel"]["value"]:
			fieldID = 'S_KEEPER_1-'+keeperURI.rsplit('/', 1)[-1]
			data[fieldID] = defaultdict(dict)
			data[fieldID][keeperURI.rsplit('/', 1)[-1]] = result["keeperLabel"]["value"].replace('%u2013','-')

		# S_KEEPER_2
		if 'address' in result:
			data['S_KEEPER_2'] = result["address"]["value"]

		# S_KEEPER_3
		if 'cityKeeperLabel' in result:
			S_KEEPER_3 = 'S_KEEPER_3-'+result["cityKeeper"]["value"].rsplit('/', 1)[-1]
			data[S_KEEPER_3] = defaultdict(dict)
			data[S_KEEPER_3][result["cityKeeper"]["value"].rsplit('/', 1)[-1]] = result["cityKeeperLabel"]["value"]

		# S_KEEPER_4
		if 'districtKeeperLabel' in result:
			S_KEEPER_4 = 'S_KEEPER_4-'+result["districtKeeper"]["value"].rsplit('/', 1)[-1]
			data[S_KEEPER_4] = defaultdict(dict)
			data[S_KEEPER_4][result["districtKeeper"]["value"].rsplit('/', 1)[-1]] = result["districtKeeperLabel"]["value"]

		# S_KEEPER_5
		if 'countryKeeperLabel' in result:
			S_KEEPER_5 = 'S_KEEPER_5-'+result["countryKeeper"]["value"].rsplit('/', 1)[-1]
			data[S_KEEPER_5] = defaultdict(dict)
			data[S_KEEPER_5][result["countryKeeper"]["value"].rsplit('/', 1)[-1]] = result["countryKeeperLabel"]["value"]

		# S_KEEPER_6
		if 'phone' in result:
			data['S_KEEPER_6'] = result["phone"]["value"]

		# S_KEEPER_7
		if 'email' in result:
			data['S_KEEPER_7'] = result["email"]["value"]

		# S_KEEPER_8
		if 'websiteKeeper' in result:
			data['S_KEEPER_8'] = result["websiteKeeper"]["value"]

		# S_COLL_2
		if 'collectionLabel' in result:
			graphID = result["g"]["value"][:-1]
			S_COLL_2 = 'S_COLL_2-'+graphID.rsplit('/', 1)[-1]
			data[S_COLL_2] = defaultdict(dict)
			data[S_COLL_2][graphID.rsplit('/', 1)[-1]] = result["collectionLabel"]["value"]
	return data


def getData(graph):
	""" get a named graph and rebuild results for modifying the record"""

	queryNGraph = '''
		PREFIX wd: <http://www.wikidata.org/entity/>
		PREFIX wdp: <http://www.wikidata.org/wiki/Property:>
		PREFIX dcterms: <http://purl.org/dc/terms/>
		PREFIX art: <https://w3id.org/artchives/>
		SELECT *
		WHERE {
			GRAPH <'''+graph+'''>
			{ 	?keeper a wd:Q31855 ; rdfs:label ?keeperLabel .
				OPTIONAL {	?keeper wdp:P969 ?address .}
				OPTIONAL {	?keeper wdp:P131 ?cityKeeper .
							?cityKeeper rdfs:label ?cityKeeperLabel .
							OPTIONAL {?cityKeeper wdp:P131 ?districtKeeper . ?districtKeeper rdfs:label ?districtKeeperLabel . }
						 }
				OPTIONAL {	?keeper wdp:P17 ?countryKeeper . ?countryKeeper rdfs:label ?countryKeeperLabel .}
				OPTIONAL {	?keeper wdp:P1329 ?phone .}
				OPTIONAL {	?keeper wdp:P968 ?email .}
				OPTIONAL {	?keeper wdp:P856 ?websiteKeeper .}
				?artHistorian a wd:Q5; rdfs:label ?artHistorianLabel .
				OPTIONAL {	?artHistorian wdp:P569 ?birthDate ; wdp:P570 ?deathDate . }
				OPTIONAL {	?artHistorian wdp:P106 ?role . ?role rdfs:label ?roleLabel . }
				OPTIONAL {	?artHistorian wdp:P27 ?countryCreator . ?countryCreator rdfs:label ?countryCreatorLabel . }
				OPTIONAL {	?artHistorian dcterms:description ?bio . }
				OPTIONAL {	?artHistorian wdp:P921 ?bioSubject . ?bioSubject rdfs:label ?bioSubjectLabel . }
				OPTIONAL {	?artHistorian wdp:P800 ?artBiblioRef . ?artBiblioRef rdfs:label ?artBiblioRefLabel . }
				OPTIONAL {	?otherbiblioRef wdp:P921 ?artHistorian ; rdfs:label ?otherbiblioRefLabel . }

			}

		}
		'''

	queryNGraph2 = '''
	PREFIX wd: <http://www.wikidata.org/entity/>
	PREFIX wdp: <http://www.wikidata.org/wiki/Property:>
	PREFIX dcterms: <http://purl.org/dc/terms/>
	PREFIX art: <https://w3id.org/artchives/>
	SELECT *
	WHERE {
		GRAPH <'''+graph+'''>
		{
			?collection rdf:type wd:Q9388534 ; rdfs:label ?collectionLabel .
			OPTIONAL {	?collection wdp:P217 ?refCode .}
			OPTIONAL {	?collection wdp:P1319 ?earlyDateCollection .}
			OPTIONAL {	?collection wdp:P1326 ?lateDateCollection .}
			OPTIONAL {	?collection wdp:P1436 ?extent .}
			OPTIONAL {	?collection art:hasNotesOnSystemOfArrangement ?arrangement . }
			OPTIONAL {	?collection art:hasMainObjectType ?mainType . ?mainType rdfs:label ?mainTypeLabel . }
			OPTIONAL {	?collection art:hasOtherObjectType ?otherType . ?otherType rdfs:label ?otherTypeLabel . }
			OPTIONAL {	?collection art:hasNotesOnScopeAndContent ?scope . }
			OPTIONAL {	?collection art:hasScopeAndContentSubject ?scopeSubject . ?scopeSubject rdfs:label ?scopeSubjectLabel . }
			OPTIONAL {	?collection art:hasHistoricalNotes ?history .}
			OPTIONAL {	?collection art:hasAcquisitionType ?acquisitionType . ?acquisitionType rdfs:label ?acquisitionTypeLabel . }
			OPTIONAL {	?collection wdp:P571 ?acquisitionYear . }
			OPTIONAL {	?collection wdp:P485 ?location . ?location rdfs:label ?locationLabel . }
			OPTIONAL {	?collection art:hasAccessConditions ?accessLabel . }
			OPTIONAL {	?collection wdp:P275 ?reproduction . ?reproduction rdfs:label ?reproductionLabel . }
			OPTIONAL {	?collection art:hasNotesOnFindingAid ?findingAid . }
			OPTIONAL {	?collection art:hasCataloguingStandard ?standard . ?standard rdfs:label ?standardLabel . }
			OPTIONAL {	?biblioColl wdp:P921 ?collection ; rdfs:label ?biblioCollLabel . }
			OPTIONAL {	?collection art:hasFirstLink ?collWebsite1 . ?collWebsite1 rdfs:comment ?collWebsiteLabel1.}
			OPTIONAL {	?collection art:hasSecondLink ?collWebsite2 . ?collWebsite2 rdfs:comment ?collWebsiteLabel2.}
			OPTIONAL {	?collection art:hasThirdLink ?collWebsite3 . ?collWebsite3 rdfs:comment ?collWebsiteLabel3.}
			OPTIONAL {	?collection art:hasAggregator ?aggregator . ?aggregator rdfs:label ?aggregatorLabel . }
			OPTIONAL {	?collection wdp:P793 ?event . ?event rdfs:label ?eventLabel . }
			OPTIONAL {	?collection art:hasOtherNotes ?otherNotes .}
			OPTIONAL {	?collection art:hasNotesOnOtherNuclei ?otherNuclei .}
		}

	}
	'''

	queryNGraph3 = '''
	PREFIX wd: <http://www.wikidata.org/entity/>
	PREFIX wdp: <http://www.wikidata.org/wiki/Property:>
	PREFIX dcterms: <http://purl.org/dc/terms/>
	PREFIX art: <https://w3id.org/artchives/>
	SELECT *
	WHERE {
		GRAPH <'''+graph+'''>
		{
			?collection rdf:type wd:Q9388534 ; rdfs:label ?collectionLabel .
			OPTIONAL {	?collection art:hasSubjectPeriod ?period . ?period rdfs:label ?periodLabel . }
			OPTIONAL {	?collection art:hasSubjectGenre ?genre . ?genre rdfs:label ?genreLabel . }
			OPTIONAL {	?collection art:hasSubjectArtist ?artist . ?artist rdfs:label ?artistLabel . }
			OPTIONAL {	?collection art:hasSubjectObject ?object . ?object rdfs:label ?objectLabel . }
			OPTIONAL {	?collection art:hasSubjectArtwork ?artwork . ?artwork rdfs:label ?artworkLabel . }
			OPTIONAL {	?collection art:hasSubjectPeople ?people . ?people rdfs:label ?peopleLabel . }
		}

	}
	'''

	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(queryNGraph)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(queryNGraph2)
	sparql.setReturnFormat(JSON)
	results2 = sparql.query().convert()

	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(queryNGraph3)
	sparql.setReturnFormat(JSON)
	results3 = sparql.query().convert()

	data = {}
	# S_KEEPER_1
	for result in results["results"]["bindings"]:
		if result["keeper"]["value"] and result["keeperLabel"]["value"]:
			fieldID = 'S_KEEPER_1-'+result["keeper"]["value"].rsplit('/', 1)[-1]
			data[fieldID] = defaultdict(dict)
			data[fieldID][result["keeper"]["value"].rsplit('/', 1)[-1]] = result["keeperLabel"]["value"]

		# S_KEEPER_2
		if 'address' in result:
			data['S_KEEPER_2'] = result["address"]["value"]

		# S_KEEPER_3
		if 'cityKeeperLabel' in result:
			S_KEEPER_3 = 'S_KEEPER_3-'+result["cityKeeper"]["value"].rsplit('/', 1)[-1]
			data[S_KEEPER_3] = defaultdict(dict)
			data[S_KEEPER_3][result["cityKeeper"]["value"].rsplit('/', 1)[-1]] = result["cityKeeperLabel"]["value"]

		# S_KEEPER_4
		if 'districtKeeperLabel' in result:
			S_KEEPER_4 = 'S_KEEPER_4-'+result["districtKeeper"]["value"].rsplit('/', 1)[-1]
			data[S_KEEPER_4] = defaultdict(dict)
			data[S_KEEPER_4][result["districtKeeper"]["value"].rsplit('/', 1)[-1]] = result["districtKeeperLabel"]["value"]

		# S_KEEPER_5
		if 'countryKeeperLabel' in result:
			S_KEEPER_5 = 'S_KEEPER_5-'+result["countryKeeper"]["value"].rsplit('/', 1)[-1]
			data[S_KEEPER_5] = defaultdict(dict)
			data[S_KEEPER_5][result["countryKeeper"]["value"].rsplit('/', 1)[-1]] = result["countryKeeperLabel"]["value"]

		# S_KEEPER_6
		if 'phone' in result:
			data['S_KEEPER_6'] = result["phone"]["value"]

		# S_KEEPER_7
		if 'email' in result:
			data['S_KEEPER_7'] = result["email"]["value"]

		# S_KEEPER_8
		if 'websiteKeeper' in result:
			data['S_KEEPER_8'] = result["websiteKeeper"]["value"]

		# S_CREATOR_1
		if 'artHistorianLabel' in result:
			S_CREATOR_1 = 'S_CREATOR_1-'+result["artHistorian"]["value"].rsplit('/', 1)[-1]
			data[S_CREATOR_1] = defaultdict(dict)
			data[S_CREATOR_1][result["artHistorian"]["value"].rsplit('/', 1)[-1]] = result["artHistorianLabel"]["value"]

		# S_CREATOR_2
		if 'birthDate' in result and 'deathDate' in result:
			data['S_CREATOR_2'] = result["birthDate"]["value"]+'-'+result["deathDate"]["value"]
		elif 'birthDate' in result and 'deathDate' not in result:
			data['S_CREATOR_2'] = result["birthDate"]["value"]+'-'
		elif 'deathDate' in result and 'birthDate' not in result:
			data['S_CREATOR_2'] = '-'+result["deathDate"]["value"]

		# S_CREATOR_3
		if 'roleLabel' in result:
			S_CREATOR_3 = 'S_CREATOR_3-'+result["role"]["value"].rsplit('/', 1)[-1]
			data[S_CREATOR_3] = defaultdict(dict)
			data[S_CREATOR_3][result["role"]["value"].rsplit('/', 1)[-1]] = result["roleLabel"]["value"]

		# S_CREATOR_4
		if 'countryCreatorLabel' in result:
			S_CREATOR_4 = 'S_CREATOR_4-'+result["countryCreator"]["value"].rsplit('/', 1)[-1]
			data[S_CREATOR_4] = defaultdict(dict)
			data[S_CREATOR_4][result["countryCreator"]["value"].rsplit('/', 1)[-1]] = result["countryCreatorLabel"]["value"]

		# S_CREATOR_5
		if 'bio' in result:
			data['S_CREATOR_5'] = result["bio"]["value"]

		if 'bioSubjectLabel' in result:
			S_CREATOR_5 = 'S_CREATOR_5-'+result["bioSubject"]["value"].rsplit('/', 1)[-1]
			data[S_CREATOR_5] = defaultdict(dict)
			data[S_CREATOR_5][result["bioSubject"]["value"].rsplit('/', 1)[-1]] = result["bioSubjectLabel"]["value"]

		# S_CREATOR_6
		if 'artBiblioRefLabel' in result:
			data['S_CREATOR_6'] = result["artBiblioRefLabel"]["value"]
			# S_CREATOR_6 = 'S_CREATOR_6-'+result["artBiblioRef"]["value"].rsplit('/', 1)[-1]
			# data[S_CREATOR_6] = defaultdict(dict)
			# data[S_CREATOR_6][result["artBiblioRef"]["value"].rsplit('/', 1)[-1]] = result["artBiblioRefLabel"]["value"]

		# S_CREATOR_7
		if 'otherbiblioRefLabel' in result:
			data['S_CREATOR_7'] = result["otherbiblioRefLabel"]["value"]
			# S_CREATOR_7 = 'S_CREATOR_7-'+result["otherbiblioRef"]["value"].rsplit('/', 1)[-1]
			# data[S_CREATOR_7] = defaultdict(dict)
			# data[S_CREATOR_7][result["otherbiblioRef"]["value"].rsplit('/', 1)[-1]] = result["otherbiblioRefLabel"]["value"]

	for result in results2["results"]["bindings"]:
		# S_COLL_1
		if 'refCode' in result:
			data['S_COLL_1'] = result["refCode"]["value"]

		# S_COLL_2
		if 'collectionLabel' in result:
			data['S_COLL_2'] = result["collectionLabel"]["value"]

		# S_COLL_3
		if 'earlyDateCollection' in result and 'lateDateCollection' in result:
			data['S_COLL_3'] = result["earlyDateCollection"]["value"]+'-'+result["lateDateCollection"]["value"]
		elif 'earlyDateCollection' in result and 'lateDateCollection' not in result:
			data['S_COLL_3'] = result["earlyDateCollection"]["value"]+'-'
		elif 'earlyDateCollection' not in result and 'lateDateCollection' in result:
			data['S_COLL_3'] = '-'+result["lateDateCollection"]["value"]

		# S_COLL_4
		if 'extent' in result:
			data['S_COLL_4'] = result["extent"]["value"]

		# S_COLL_5
		if 'arrangement' in result:
			data['S_COLL_5'] = result["arrangement"]["value"]

		# S_COLL_6
		if 'mainTypeLabel' in result:
			S_COLL_6 = 'S_COLL_6-'+result["mainType"]["value"].rsplit('/', 1)[-1]
			data[S_COLL_6] = defaultdict(dict)
			data[S_COLL_6][result["mainType"]["value"].rsplit('/', 1)[-1]] = result["mainTypeLabel"]["value"]

		# S_COLL_7
		if 'otherTypeLabel' in result:
			S_COLL_7 = 'S_COLL_7-'+result["otherType"]["value"].rsplit('/', 1)[-1]
			data[S_COLL_7] = defaultdict(dict)
			data[S_COLL_7][result["otherType"]["value"].rsplit('/', 1)[-1]] = result["otherTypeLabel"]["value"]

		# S_COLL_8
		if 'scope' in result:
			data['S_COLL_8'] = result["scope"]["value"]

		if 'scopeSubjectLabel' in result:
			S_COLL_8 = 'S_COLL_8-'+result["scopeSubject"]["value"].rsplit('/', 1)[-1]
			data[S_COLL_8] = defaultdict(dict)
			data[S_COLL_8][result["scopeSubject"]["value"].rsplit('/', 1)[-1]] = result["scopeSubjectLabel"]["value"]

		# S_COLL_9
		if 'history' in result:
			data['S_COLL_9'] = result["history"]["value"]

		# S_COLL_10
		if 'acquisitionTypeLabel' in result:
			S_COLL_10 = 'S_COLL_10-'+result["acquisitionType"]["value"].rsplit('/', 1)[-1]
			data[S_COLL_10] = defaultdict(dict)
			data[S_COLL_10][result["acquisitionType"]["value"].rsplit('/', 1)[-1]] = result["acquisitionTypeLabel"]["value"]

		# S_COLL_11
		if 'acquisitionYear' in result:
			data['S_COLL_11'] = result["acquisitionYear"]["value"]

		# S_COLL_12
		if 'locationLabel' in result:
			S_COLL_12 = 'S_COLL_12-'+result["location"]["value"].rsplit('/', 1)[-1]
			data[S_COLL_12] = defaultdict(dict)
			data[S_COLL_12][result["location"]["value"].rsplit('/', 1)[-1]] = result["locationLabel"]["value"]

		# S_COLL_13
		if 'accessLabel' in result:
			data['S_COLL_13'] = result["accessLabel"]["value"]

		# S_COLL_14
		if 'reproductionLabel' in result:
			S_COLL_14 = 'S_COLL_14-'+result["reproduction"]["value"].rsplit('/', 1)[-1]
			data[S_COLL_14] = defaultdict(dict)
			data[S_COLL_14][result["reproduction"]["value"].rsplit('/', 1)[-1]] = result["reproductionLabel"]["value"]

		# S_COLL_15
		if 'findingAid' in result:
			data['S_COLL_15'] = result["findingAid"]["value"]

		# S_COLL_16
		if 'standardLabel' in result:
			S_COLL_16 = 'S_COLL_16-'+result["standard"]["value"].rsplit('/', 1)[-1]
			data[S_COLL_16] = defaultdict(dict)
			data[S_COLL_16][result["standard"]["value"].rsplit('/', 1)[-1]] = result["standardLabel"]["value"]

		# S_COLL_17
		if 'biblioCollLabel' in result:
			data['S_COLL_17'] = result["biblioCollLabel"]["value"]
			# S_COLL_17 = 'S_COLL_17-'+result["biblioColl"]["value"].rsplit('/', 1)[-1]
			# data[S_COLL_17] = defaultdict(dict)
			# data[S_COLL_17][result["biblioColl"]["value"].rsplit('/', 1)[-1]] = result["biblioCollLabel"]["value"]

		# S_COLL_18_n
		if 'collWebsite1' in result:
			website = result["collWebsite1"]["value"]
			data['S_COLL_18_1'] = website
			# S_COLL_18_n_desc
			if 'collWebsiteLabel1' in result:
				desc = result["collWebsiteLabel1"]["value"]
				data['S_COLL_18_1_desc'] = desc
		if 'collWebsite2' in result:
			website2 = result["collWebsite2"]["value"]
			data['S_COLL_18_2'] = website2
			# S_COLL_18_n_desc
			if 'collWebsiteLabel2' in result:
				desc2 = result["collWebsiteLabel2"]["value"]
				data['S_COLL_18_2_desc'] = desc2
		if 'collWebsite3' in result:
			website3 = result["collWebsite3"]["value"]
			data['S_COLL_18_3'] = website3
			# S_COLL_18_n_desc
			if 'collWebsiteLabel3' in result:
				desc3 = result["collWebsiteLabel3"]["value"]
				data['S_COLL_18_3_desc'] = desc3

		# S_COLL_19
		if 'aggregatorLabel' in result:
			S_COLL_19 = 'S_COLL_19-'+result["aggregator"]["value"].rsplit('/', 1)[-1]
			data[S_COLL_19] = defaultdict(dict)
			data[S_COLL_19][result["aggregator"]["value"].rsplit('/', 1)[-1]] = result["aggregatorLabel"]["value"]

		# S_COLL_20
		if 'eventLabel' in result:
			S_COLL_20 = 'S_COLL_20-'+result["event"]["value"].rsplit('/', 1)[-1]
			data[S_COLL_20] = defaultdict(dict)
			data[S_COLL_20][result["event"]["value"].rsplit('/', 1)[-1]] = result["eventLabel"]["value"]

		# S_COLL_21
		if 'otherNotes' in result:
			data['S_COLL_21'] = result["otherNotes"]["value"]

		# S_COLL_22
		if 'otherNuclei' in result:
			data['S_COLL_22'] = result["otherNuclei"]["value"]

	for result in results3["results"]["bindings"]:
		# S_SUBJ_1
		if 'periodLabel' in result:
			S_SUBJ_1 = 'S_SUBJ_1-'+result["period"]["value"].rsplit('/', 1)[-1]
			data[S_SUBJ_1] = defaultdict(dict)
			data[S_SUBJ_1][result["period"]["value"].rsplit('/', 1)[-1]] = result["periodLabel"]["value"]

		# S_SUBJ_2
		if 'genreLabel' in result:
			S_SUBJ_2 = 'S_SUBJ_2-'+result["genre"]["value"].rsplit('/', 1)[-1]
			data[S_SUBJ_2] = defaultdict(dict)
			data[S_SUBJ_2][result["genre"]["value"].rsplit('/', 1)[-1]] = result["genreLabel"]["value"]

		# S_SUBJ_3
		# if result.has_key('placeLabel'):
		# 	S_SUBJ_3 = 'S_SUBJ_3-'+result["place"]["value"].rsplit('/', 1)[-1]
		# 	data[S_SUBJ_3] = defaultdict(dict)
		# 	data[S_SUBJ_3][result["place"]["value"].rsplit('/', 1)[-1]] = result["placeLabel"]["value"]

		# S_SUBJ_4
		if 'artistLabel' in result:
			S_SUBJ_4 = 'S_SUBJ_4-'+result["artist"]["value"].rsplit('/', 1)[-1]
			data[S_SUBJ_4] = defaultdict(dict)
			data[S_SUBJ_4][result["artist"]["value"].rsplit('/', 1)[-1]] = result["artistLabel"]["value"]

		# S_SUBJ_5
		if 'objectLabel' in result:
			S_SUBJ_5 = 'S_SUBJ_5-'+result["object"]["value"].rsplit('/', 1)[-1]
			data[S_SUBJ_5] = defaultdict(dict)
			data[S_SUBJ_5][result["object"]["value"].rsplit('/', 1)[-1]] = result["objectLabel"]["value"]

		# S_SUBJ_6
		if 'artworkLabel' in result:
			S_SUBJ_6 = 'S_SUBJ_6-'+result["artwork"]["value"].rsplit('/', 1)[-1]
			data[S_SUBJ_6] = defaultdict(dict)
			data[S_SUBJ_6][result["artwork"]["value"].rsplit('/', 1)[-1]] = result["artworkLabel"]["value"]

		# S_SUBJ_7
		if 'peopleLabel' in result:
			S_SUBJ_4 = 'S_SUBJ_7-'+result["people"]["value"].rsplit('/', 1)[-1]
			data[S_SUBJ_4] = defaultdict(dict)
			data[S_SUBJ_4][result["people"]["value"].rsplit('/', 1)[-1]] = result["peopleLabel"]["value"]

	return data


def deleteRecord(graph):
	""" delete a named graph and related record """

	clearGraph = ' CLEAR GRAPH <'+graph+'> '
	deleteGraph = ' DROP GRAPH <'+graph+'> '
	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(clearGraph)
	sparql.method = 'POST'
	sparql.query()
	sparql.setQuery(deleteGraph)
	sparql.method = 'POST'
	sparql.query()


def clearGraph(graph):
	clearGraph = ' CLEAR GRAPH <'+graph+'> '
	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(clearGraph)
	sparql.method = 'POST'
	sparql.query()



def getBibliography():
	records = {}
	sparql = SPARQLWrapper(conf.artchivesEndpoint)
	sparql.setQuery(queryBiblio)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	for result in results["results"]["bindings"]:
 		records[result["nameCollection"]["value"].lstrip().rstrip()] = [result["otherbiblioRefLabel"]["value"].split(";"), result["collbiblioLabel"]["value"].split(";")]
	 	for k, v in records.items():
	 		records[k] = v
	sorted_dict = dict(sorted(records.items(), key=operator.itemgetter(0)))
	return sorted_dict
