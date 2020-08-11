# -*- coding: utf-8 -*-
import web , datetime , os, time, re, cgi, rdflib, conf , urllib.parse , queries
from rdflib import URIRef , XSD, Namespace , Literal
from rdflib.namespace import OWL, DC , DCTERMS, RDF , RDFS
from rdflib.plugins.sparql import prepareQuery
from SPARQLWrapper import SPARQLWrapper, JSON
from web import form
from pymantic import sparql

WD = Namespace("http://www.wikidata.org/entity/")
WDP = Namespace("http://www.wikidata.org/wiki/Property:")
OL = Namespace("http://openlibrary.org/works/")
ULAN = Namespace("http://vocab.getty.edu/ulan/")
AAT = Namespace("http://vocab.getty.edu/aat/")
PROV = Namespace("http://www.w3.org/ns/prov#")
base = 'https://w3id.org/artchives/'

server = sparql.SPARQLServer(conf.artchivesEndpoint)
dir_path = os.path.dirname(os.path.realpath(__file__))


def clean_to_uri(stringa):
	""" given a string return a partial URI"""
	uri = re.sub('ä', 'a', stringa.strip().lower())
	uri = re.sub('à', 'a', uri)
	uri = re.sub('è', 'e', uri)
	uri = re.sub('é', 'e', uri)
	uri = re.sub('ì', 'i', uri)
	uri = re.sub('ò', 'o', uri)
	uri = re.sub('ù', 'u', uri)
	uri = re.sub('[^a-zA-Z\s]', '', uri)
	uri = re.sub('\s', '-', uri)
	return uri


def getValuesFromFields(fieldPrefix, recordData):
	""" returs a set of tuples including ID and label for the selected fields"""
	results = set()
	for key, value in recordData.items():
		if key.startswith(fieldPrefix):
			values = value.split(',', 1)
			results.add(( values[0], urllib.parse.unquote(values[1]) )) # (id, label)
	return results

def getURLsFromField(myString):
	"regex to extract URLs and description. Returns a list of tuples (uri, desc)"
	uriList = []
	if ';' in myString:
		uris = myString.split(';')
		for uri in uris:
			if uri != '' and uri !=' ':
				desc = re.sub( re.compile(r'(https?://[^\s]+)'), '', uri ).rstrip().lstrip()
				uriList.append( (re.search(r'(https?://[^\s]+)', uri).group(0), desc) )
	else:
		desc = re.sub( re.compile(r'(https?://[^\s]+)'), '', myString ).rstrip().lstrip()
		uriList.append( (re.search(r'(https?://[^\s]+)', myString).group(0), desc) )
	return uriList

def getRightURIbase(value):
	"dispatcher URIs"
	if value.startswith('Q'):
		return WD
	elif value.startswith('OL'):
		return OL
	else:
		return base


def gettyAATbase(value):
	"dispatcher URIs"
	if value.startswith('MD'):
		return base
	elif value.startswith('Q'):
		return WD
	else:
		return AAT


def gettyULANbase(value):
	"dispatcher URIs"
	if value.startswith('MD'):
		return base
	elif value.startswith('Q'):
		return WD
	else:
		return ULAN


def artchivesToWD(recordData, userID, stage, graphToClear=None):
	""" given input data creates a named graph and a rdf file according to wikidata and artchives models"""
	recordID = recordData.recordID
	graph_name = recordID.split("record-",1)[1]
	wd = rdflib.Graph(identifier=URIRef(base+graph_name+'/'))
	if stage == 'not modified':
		wd.add(( URIRef(base+graph_name+'/'), PROV.wasGeneratedBy, URIRef(base+userID) ))
		wd.add(( URIRef(base+userID), RDFS.label , Literal(userID.replace('-dot-','.').replace('-at-', '@') ) ))
	else:
		# modifier
		wd.add(( URIRef(base+graph_name+'/'), PROV.wasInfluencedBy, URIRef(base+userID) ))
		wd.add(( URIRef(base+userID), RDFS.label , Literal(userID.replace('-dot-','.').replace('-at-', '@') ) ))
		# creator
		creatorIRI, creatorLabel = queries.getRecordCreator(graphToClear)
		if creatorIRI is not None and creatorLabel is not None:
			wd.add(( URIRef(base+graph_name+'/'), PROV.wasGeneratedBy, URIRef(creatorIRI) ))
			wd.add(( URIRef(creatorIRI), RDFS.label , Literal(creatorLabel ) ))
		queries.clearGraph(graphToClear)
	wd.add(( URIRef(base+graph_name+'/'), PROV.generatedAtTime, Literal(datetime.datetime.now(),datatype=XSD.dateTime)  ))
	wd.add(( URIRef(base+graph_name+'/'), URIRef(base + 'publicationStage'), Literal(stage, datatype="http://www.w3.org/2001/XMLSchema#string")  ))

	# S_KEEPER_1
	keepers = getValuesFromFields("S_KEEPER_1-", recordData)
	if len(keepers) == 0:
		keepers.add( ( 'keeper'+str(time.time()).replace('.','-'), 'none') )
	else:
		keepers = keepers
	for keeper in keepers:
		keeperURI = getRightURIbase(keeper[0])+keeper[0]
		wd.add(( URIRef( keeperURI ), RDF.type, URIRef(WD.Q31855) ))
		wd.add(( URIRef( keeperURI ), RDFS.label, Literal(keeper[1].lstrip().rstrip(), datatype="http://www.w3.org/2001/XMLSchema#string") ))
		if keeper[0].startswith('MD'):
			wd.add(( URIRef( keeperURI ), RDFS.comment, Literal('Cultural institution', datatype="http://www.w3.org/2001/XMLSchema#string") ))

		# S_KEEPER_2
		address = recordData.S_KEEPER_2
		if address:
			wd.add(( URIRef( keeperURI ), WDP.P969, Literal(address, datatype="http://www.w3.org/2001/XMLSchema#string") ))

		# S_KEEPER_3
		citiesKeeper = getValuesFromFields("S_KEEPER_3-", recordData)
		if citiesKeeper:
			for cityKeeper in citiesKeeper:
				cityURI = getRightURIbase(cityKeeper[0])+cityKeeper[0]
				wd.add(( URIRef( keeperURI ), WDP.P131, URIRef(cityURI) ))
				wd.add(( URIRef( cityURI ), RDFS.label, Literal( cityKeeper[1] ) ))

		# S_KEEPER_4
		districtsKeeper = getValuesFromFields("S_KEEPER_4-", recordData)
		if districtsKeeper:
			for districtKeeper in districtsKeeper:
				districtURI = getRightURIbase(districtKeeper[0])+districtKeeper[0]
				wd.add(( URIRef( cityURI ), WDP.P131, URIRef( districtURI ) ))
				wd.add(( URIRef( districtURI ), RDFS.label, Literal( districtKeeper[1] ) ))

		# S_KEEPER_5
		countriesKeeper = getValuesFromFields("S_KEEPER_5-", recordData)
		if countriesKeeper:
			for countryKeeper in countriesKeeper:
				countryURI = getRightURIbase(countryKeeper[0])+countryKeeper[0]
				wd.add(( URIRef( keeperURI ), WDP.P17, URIRef( countryURI ) ))
				wd.add(( URIRef( countryURI ), RDFS.label, Literal( countryKeeper[1] ) ))

		# S_KEEPER_6
		phone = recordData.S_KEEPER_6
		if phone:
			wd.add(( URIRef( keeperURI ), WDP.P1329, Literal(phone, datatype="http://www.w3.org/2001/XMLSchema#string") ))

		# S_KEEPER_7
		email = recordData.S_KEEPER_7
		if email:
			wd.add(( URIRef( keeperURI ), WDP.P968, Literal(email, datatype="http://www.w3.org/2001/XMLSchema#string") ))

		# S_KEEPER_8
		websiteKeeper = recordData.S_KEEPER_8
		if websiteKeeper:
			wd.add(( URIRef( keeperURI ), WDP.P856, URIRef(websiteKeeper) ))

	# S_CREATOR_1
	creators = getValuesFromFields("S_CREATOR_1-", recordData)
	if len(creators) == 0:
		creators.add( ( 'creator'+str(time.time()).replace('.','-'), 'none') )
	else:
		creators = creators
	for creator in creators:
		creatorURI = getRightURIbase(creator[0])+creator[0]
		wd.add(( URIRef( creatorURI ), RDF.type, URIRef(WD.Q5) ))
		wd.add(( URIRef( creatorURI ), RDFS.label, Literal(creator[1].lstrip().rstrip(), datatype="http://www.w3.org/2001/XMLSchema#string") ))
		wd.add(( URIRef(base+graph_name+'/'), RDFS.label, Literal(creator[1].lstrip()) ))
		# label for wikidata
		if creator[0].startswith('MD') :
			wd.add(( URIRef( creatorURI ), RDFS.comment, Literal( 'Art historian', datatype="http://www.w3.org/2001/XMLSchema#string") ))

		# S_CREATOR_2
		datesCreator = recordData.S_CREATOR_2
		if datesCreator:
			birth = re.compile('(\d{4})-', re.IGNORECASE|re.DOTALL)
			death = re.compile('-(\d{4})', re.IGNORECASE|re.DOTALL)
			matchBirth = birth.search(datesCreator)
			matchDeath = death.search(datesCreator)
			if matchBirth:
				wd.add(( URIRef( creatorURI ), WDP.P569, Literal( matchBirth.group(1), datatype="http://www.w3.org/2001/XMLSchema#gYear" ) ))
			if matchDeath:
				wd.add(( URIRef( creatorURI ), WDP.P570, Literal( matchDeath.group(1), datatype="http://www.w3.org/2001/XMLSchema#gYear" ) ))

		# S_CREATOR_3
		roles = getValuesFromFields("S_CREATOR_3-", recordData)
		if roles:
			for role in roles:
				roleURI = getRightURIbase(role[0])+role[0]
				wd.add(( URIRef( creatorURI ), WDP.P106, URIRef( roleURI ) ))
				wd.add(( URIRef( roleURI ), RDFS.label, Literal( role[1] ) ))
				if role[0].startswith('MD'):
					wd.add(( URIRef( roleURI ), RDFS.comment, Literal( 'profession' ) ))

		# S_CREATOR_4
		countriesCreator = getValuesFromFields("S_CREATOR_4-", recordData)
		if countriesCreator:
			for countryCreator in countriesCreator:
				countryCreatorURI = getRightURIbase(countryCreator[0])+countryCreator[0]
				wd.add(( URIRef( creatorURI ), WDP.P27, URIRef( countryCreatorURI ) ))
				wd.add(( URIRef( countryCreatorURI ), RDFS.label, Literal( countryCreator[1] ) ))

		# S_CREATOR_5
		bio = recordData.S_CREATOR_5
		if bio:
			wd.add(( URIRef( creatorURI ), DCTERMS.description, Literal(bio, datatype="http://www.w3.org/2001/XMLSchema#string") ))

		bioSubjects = getValuesFromFields("S_CREATOR_5-", recordData)
		if bioSubjects:
			for bioSubject in bioSubjects:
				bioSubjectURI = getRightURIbase(bioSubject[0])+bioSubject[0]
				wd.add(( URIRef( creatorURI ), WDP.P921, URIRef( bioSubjectURI ) ))
				wd.add(( URIRef( bioSubjectURI ), RDFS.label, Literal(bioSubject[1].lstrip(), datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_CREATOR_6
		artBiblio = recordData.S_CREATOR_6
		artBiblioRefURI = base+'artHistorianBibliography'
		if artBiblio:
			wd.add(( URIRef( creatorURI ), WDP.P800, URIRef(artBiblioRefURI) ))
			wd.add(( URIRef( artBiblioRefURI ), RDFS.label, Literal(artBiblio.lstrip(), datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
			# for artBiblioRef in artBiblio:
			# 	artBiblioRefURI = getRightURIbase(artBiblioRef[0])+artBiblioRef[0]
			# 	wd.add(( URIRef( creatorURI ), WDP.P800, URIRef( artBiblioRefURI ) ))
			# 	wd.add(( URIRef( artBiblioRefURI ), RDFS.label, Literal(artBiblioRef[1].lstrip(), datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_CREATOR_7
		biblioOnArt = recordData.S_CREATOR_7
		biblioOnArtURI = base+'biblioOnArtHistorian'
		if biblioOnArt:
			wd.add(( URIRef( biblioOnArtURI ), WDP.P921, URIRef( creatorURI ) ))
			wd.add(( URIRef( biblioOnArtURI ), RDFS.label, Literal(biblioOnArt.lstrip(), datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
		# biblioOnArt = getValuesFromFields("S_CREATOR_7-", recordData)
		# if biblioOnArt:
			# for biblioRefOnArt in biblioOnArt:
			# 	biblioRefOnArtURI = getRightURIbase(biblioRefOnArt[0])+biblioRefOnArt[0]
			# 	wd.add(( URIRef( biblioRefOnArtURI ), WDP.P921, URIRef( creatorURI ) ))
			# 	wd.add(( URIRef( biblioRefOnArtURI ), RDFS.label, Literal(biblioRefOnArt[1].lstrip(), datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_2
		collectionData = list()
		collection = recordData.S_COLL_2
		if collection:
			collectionData.append( ('collection'+clean_to_uri(collection), collection) )
		else:
			collectionData.append( ('collection'+str(time.time()).replace('.','-'), 'no name' ) )
		collectionURI = base+collectionData[0][0]
		wd.add(( URIRef( collectionURI ), RDF.type, URIRef(WD.Q9388534) ))
		wd.add(( URIRef( collectionURI ), RDFS.label, Literal( collectionData[0][1].lstrip().rstrip(), datatype="http://www.w3.org/2001/XMLSchema#string") ))
		wd.add(( URIRef( collectionURI ), WDP.P170, URIRef( creatorURI ) ))
		wd.add(( URIRef( collectionURI ), WDP.P127, URIRef( keeperURI ) ))
		wd.add(( URIRef( keeperURI ), WDP.P1830, URIRef( collectionURI ) ))
		wd.add(( URIRef( collectionURI ), RDFS.comment, Literal( 'archival collection', datatype="http://www.w3.org/2001/XMLSchema#string") ))

		# S_COLL_1
		collectionRef = recordData.S_COLL_1
		if collectionRef:
			wd.add(( URIRef( collectionURI ), WDP.P217, Literal( collectionRef, datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_3
		datesCollection = recordData.S_COLL_3
		if datesCollection:
			early = re.compile('(\d{4})-', re.IGNORECASE|re.DOTALL)
			late = re.compile('-(\d{4})', re.IGNORECASE|re.DOTALL)
			matchEarly = early.search(datesCollection)
			matchLate = late.search(datesCollection)
			if matchEarly:
				wd.add(( URIRef( collectionURI ), WDP.P1319, Literal( matchEarly.group(1), datatype="http://www.w3.org/2001/XMLSchema#gYear" ) ))
			if matchLate:
				wd.add(( URIRef( collectionURI ), WDP.P1326, Literal( matchLate.group(1), datatype="http://www.w3.org/2001/XMLSchema#gYear" ) ))

		# S_COLL_4
		extent = recordData.S_COLL_4
		if extent:
			wd.add(( URIRef( collectionURI ), WDP.P1436, Literal( extent, datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_5
		arrangement = recordData.S_COLL_5
		if arrangement:
			wd.add(( URIRef( collectionURI ), URIRef(base+'hasNotesOnSystemOfArrangement'), Literal( arrangement, datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_6
		mainTypes = getValuesFromFields("S_COLL_6-", recordData)
		if mainTypes:
			for mainType in mainTypes:
				mainTypeURI = getRightURIbase(mainType[0])+mainType[0]
				wd.add(( URIRef( collectionURI ), URIRef( base+'hasMainObjectType'), URIRef( mainTypeURI ) ))
				wd.add(( URIRef( mainTypeURI ), RDFS.label, Literal(mainType[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
				if mainType[0].startswith('MD'):
					wd.add(( URIRef( mainTypeURI ), RDFS.comment, Literal('object', datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_7
		otherTypes = getValuesFromFields("S_COLL_7-", recordData)
		if otherTypes:
			for otherType in otherTypes:
				otherTypeURI = getRightURIbase(otherType[0])+otherType[0]
				wd.add(( URIRef( collectionURI ), URIRef( base+'hasOtherObjectType'), URIRef( otherTypeURI ) ))
				wd.add(( URIRef( otherTypeURI ), RDFS.label, Literal(otherType[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
				if otherType[0].startswith('MD'):
					wd.add(( URIRef( otherTypeURI ), RDFS.comment, Literal('object', datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_8
		scope = recordData.S_COLL_8
		if scope:
			wd.add(( URIRef( collectionURI ), URIRef(base+'hasNotesOnScopeAndContent'), Literal( scope, datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		scopeSubjects = getValuesFromFields("S_COLL_8-", recordData)
		if scopeSubjects:
			for scopeSubject in scopeSubjects:
				scopeSubjectURI = getRightURIbase(scopeSubject[0])+scopeSubject[0]
				# wd.add(( URIRef( collectionURI ), WDP.P921, URIRef( creatorURI ) ))
				wd.add(( URIRef( collectionURI ), WDP.P921, URIRef( scopeSubjectURI ) ))
				wd.add(( URIRef( collectionURI ), URIRef(base+'hasScopeAndContentSubject'), URIRef( scopeSubjectURI ) ))
				wd.add(( URIRef( scopeSubjectURI ), RDFS.label, Literal(scopeSubject[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_9
		history = recordData.S_COLL_9
		if history:
			wd.add(( URIRef( collectionURI ), URIRef(base+'hasHistoricalNotes'), Literal( history, datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_10
		acquisitionTypes = getValuesFromFields("S_COLL_10-", recordData)
		if acquisitionTypes:
			for acquisitionType in acquisitionTypes:
				acquisitionTypeURI = getRightURIbase(acquisitionType[0])+acquisitionType[0]
				wd.add(( URIRef( collectionURI ), URIRef( base+'hasAcquisitionType'), URIRef( acquisitionTypeURI ) ))
				wd.add(( URIRef( acquisitionTypeURI ), RDFS.label, Literal(acquisitionType[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
				if acquisitionType[0].startswith('MD'):
					wd.add(( URIRef( acquisitionTypeURI ), RDFS.comment, Literal('acquisition type', datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_11
		dateAcquisition = recordData.S_COLL_11
		if dateAcquisition:
			year = re.compile('(\d{4})', re.IGNORECASE|re.DOTALL)
			matchYear = year.search(dateAcquisition)
			if matchYear:
				wd.add(( URIRef( collectionURI ), WDP.P571, Literal( matchYear.group(1), datatype="http://www.w3.org/2001/XMLSchema#gYear" ) ))

		# S_COLL_12
		locations = getValuesFromFields("S_COLL_12-", recordData)
		if locations:
			for location in locations:
				locationURI = getRightURIbase(location[0])+location[0]
				wd.add(( URIRef( collectionURI ), WDP.P485, URIRef( locationURI ) ))
				wd.add(( URIRef( locationURI ), RDFS.label, Literal(location[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_13
		access = recordData.S_COLL_13
		if access:
			wd.add(( URIRef( collectionURI ), URIRef(base+'hasAccessConditions'), Literal(access, datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_14
		reproductionTypes = getValuesFromFields("S_COLL_14-", recordData)
		if reproductionTypes:
			for reproductionType in reproductionTypes:
				reproductionTypeURI = getRightURIbase(reproductionType[0])+reproductionType[0]
				wd.add(( URIRef( collectionURI ), WDP.P275, URIRef( reproductionTypeURI ) ))
				wd.add(( URIRef( reproductionTypeURI ), RDFS.label, Literal(reproductionType[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
				if reproductionType[0].startswith('MD'):
					wd.add(( URIRef( reproductionTypeURI ), RDFS.comment, Literal('conditions for reproduction', datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_15
		findingAid = recordData.S_COLL_15
		if findingAid:
			wd.add(( URIRef( collectionURI ), URIRef(base+'hasNotesOnFindingAid'), Literal( findingAid, datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_16
		cataloguingStandards = getValuesFromFields("S_COLL_16-", recordData)
		if cataloguingStandards:
			for cataloguingStandard in cataloguingStandards:
				cataloguingStandardURI = getRightURIbase(cataloguingStandard[0])+cataloguingStandard[0]
				wd.add(( URIRef( collectionURI ), URIRef( base+'hasCataloguingStandard'), URIRef( cataloguingStandardURI ) ))
				wd.add(( URIRef( cataloguingStandardURI ), RDFS.label, Literal(cataloguingStandard[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
				if cataloguingStandard[0].startswith('MD'):
					wd.add(( URIRef( cataloguingStandardURI ), RDFS.comment, Literal('cataloguing standard', datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_17
		biblioOnColl = recordData.S_COLL_17
		biblioOnCollURI = base+'biblioOnCollection'
		if biblioOnColl:
			wd.add(( URIRef( biblioOnCollURI ), WDP.P921, URIRef( collectionURI ) ))
			wd.add(( URIRef( biblioOnCollURI ), RDFS.label, Literal(biblioOnColl.lstrip(), datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# biblioOnColl = getValuesFromFields("S_COLL_17-", recordData)
		# if biblioOnColl:
		# 	for biblioRefOnColl in biblioOnColl:
		# 		biblioRefOnCollURI = getRightURIbase(biblioRefOnColl[0])+biblioRefOnColl[0]
		# 		wd.add(( URIRef( biblioRefOnCollURI ), WDP.P921, URIRef( collectionURI ) ))
		# 		wd.add(( URIRef( biblioRefOnCollURI ), RDFS.label, Literal(biblioRefOnColl[1].lstrip(), datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_18
		linkColl = recordData.S_COLL_18_1
		if linkColl:
			wd.add(( URIRef( collectionURI ), WDP.P973, URIRef( linkColl.strip() ) ))
			wd.add(( URIRef( collectionURI ), URIRef(base+'hasFirstLink'), URIRef( linkColl.strip() ) ))
			desc = recordData.S_COLL_18_1_desc
			if desc:
				wd.add(( URIRef( linkColl.strip() ), RDFS.comment, Literal( desc ) ))
		linkColl2 = recordData.S_COLL_18_2
		if linkColl2:
			wd.add(( URIRef( collectionURI ), WDP.P973, URIRef( linkColl2.strip() ) ))
			wd.add(( URIRef( collectionURI ), URIRef(base+'hasSecondLink'), URIRef( linkColl2.strip() ) ))
			desc2 = recordData.S_COLL_18_2_desc
			if desc2:
				wd.add(( URIRef( linkColl2.strip() ), RDFS.comment, Literal( desc2 ) ))
		linkColl3 = recordData.S_COLL_18_3
		if linkColl3:
			wd.add(( URIRef( collectionURI ), WDP.P973, URIRef( linkColl3.strip() ) ))
			wd.add(( URIRef( collectionURI ), URIRef(base+'hasThirdLink'), URIRef( linkColl3.strip() ) ))
			desc3 = recordData.S_COLL_18_3_desc
			if desc3:
				wd.add(( URIRef( linkColl3.strip() ), RDFS.comment, Literal( desc3 ) ))
			# urlList = getURLsFromField(linkColl)
			# for url, desc in urlList:
			# 	wd.add(( URIRef( collectionURI ), WDP.P973, URIRef( url ) ))
			# 	wd.add(( URIRef( url ), RDFS.label, Literal( desc ) ))

		# S_COLL_19
		aggregators = getValuesFromFields("S_COLL_19-", recordData)
		if aggregators:
			for aggregator in aggregators:
				aggregatorURI = getRightURIbase(aggregator[0])+aggregator[0]
				wd.add(( URIRef( collectionURI ), URIRef( base+'hasAggregator' ), URIRef( aggregatorURI ) ))
				wd.add(( URIRef( aggregatorURI ), RDFS.label, Literal(aggregator[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
				if aggregator[0].startswith('MD'):
					wd.add(( URIRef( aggregatorURI ), RDFS.comment, Literal('data aggregator', datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_20
		events = getValuesFromFields("S_COLL_20-", recordData)
		if events:
			for event in events:
				eventURI = getRightURIbase(event[0])+event[0]
				wd.add(( URIRef( collectionURI ), WDP.P793, URIRef( eventURI ) ))
				wd.add(( URIRef( eventURI ), RDFS.label, Literal(event[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
				if event[0].startswith('MD'):
					wd.add(( URIRef( eventURI ), RDFS.comment, Literal('event', datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_21
		otherNotes = recordData.S_COLL_21
		if otherNotes:
			wd.add(( URIRef( collectionURI ), URIRef( base+'hasOtherNotes'), Literal( otherNotes, datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_COLL_22
		otherNotesNuclei = recordData.S_COLL_22
		if otherNotesNuclei:
			wd.add(( URIRef( collectionURI ), URIRef( base+'hasNotesOnOtherNuclei'), Literal( otherNotesNuclei, datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_SUBJ_1
		periods = getValuesFromFields("S_SUBJ_1-", recordData)
		if periods:
			for period in periods:
				periodURI = gettyAATbase(period[0])+period[0]
				wd.add(( URIRef( collectionURI ), WDP.P921, URIRef( periodURI ) ))
				wd.add(( URIRef( collectionURI ), URIRef( base+'hasSubjectPeriod'), URIRef( periodURI ) ))
				wd.add(( URIRef( periodURI ), RDFS.label, Literal(period[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
				if period[0].startswith('MD'):
					wd.add(( URIRef( periodURI ), RDFS.comment, Literal('period', datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_SUBJ_2
		genres = getValuesFromFields("S_SUBJ_2-", recordData)
		if genres:
			for genre in genres:
				genreURI = getRightURIbase(genre[0])+genre[0]
				wd.add(( URIRef( collectionURI ), WDP.P921, URIRef( genreURI ) ))
				wd.add(( URIRef( collectionURI ), URIRef( base+'hasSubjectGenre'), URIRef( genreURI ) ))
				wd.add(( URIRef( genreURI ), RDFS.label, Literal(genre[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
				if genre[0].startswith('MD'):
					wd.add(( URIRef( genreURI ), RDFS.comment, Literal('artistic genre or theme', datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_SUBJ_3
		# places = getValuesFromFields("S_SUBJ_3-", recordData)
		# if places:
		# 	for place in places:
		# 		placeURI = getRightURIbase(place[0])+place[0]
		# 		wd.add(( URIRef( collectionURI ), WDP.P921, URIRef( placeURI ) ))
		# 		wd.add(( URIRef( collectionURI ), URIRef( base+'hasSubjectPlace'), URIRef( placeURI ) ))
		# 		wd.add(( URIRef( placeURI ), RDFS.label, Literal(place[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_SUBJ_4
		artists = getValuesFromFields("S_SUBJ_4-", recordData)
		if artists:
			for artist in artists:
				artistURI = gettyULANbase(artist[0])+artist[0]
				wd.add(( URIRef( collectionURI ), WDP.P921, URIRef( artistURI ) ))
				wd.add(( URIRef( collectionURI ), URIRef( base+'hasSubjectArtist'), URIRef( artistURI ) ))
				wd.add(( URIRef( artistURI ), RDFS.label, Literal(artist[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
				if artist[0].startswith('MD'):
					wd.add(( URIRef( artistURI ), RDFS.comment, Literal('artist', datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_SUBJ_5
		typesArtwork = getValuesFromFields("S_SUBJ_5-", recordData)
		if typesArtwork:
			for typeArtwork in typesArtwork:
				typeArtworkURI = gettyAATbase(typeArtwork[0])+typeArtwork[0]
				wd.add(( URIRef( collectionURI ), WDP.P921, URIRef( typeArtworkURI ) ))
				wd.add(( URIRef( collectionURI ), URIRef( base+'hasSubjectObject'), URIRef( typeArtworkURI ) ))
				wd.add(( URIRef( typeArtworkURI ), RDFS.label, Literal(typeArtwork[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
				if typeArtwork[0].startswith('MD'):
					wd.add(( URIRef( typeArtworkURI ), RDFS.comment, Literal('type of artwork', datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_SUBJ_6
		artworks = getValuesFromFields("S_SUBJ_6-", recordData)
		if artworks:
			for artwork in artworks:
				artworkURI = getRightURIbase(artwork[0])+artwork[0]
				wd.add(( URIRef( collectionURI ), WDP.P921, URIRef( artworkURI ) ))
				wd.add(( URIRef( collectionURI ), URIRef( base+'hasSubjectArtwork'), URIRef( artworkURI ) ))
				wd.add(( URIRef( artworkURI ), RDFS.label, Literal(artwork[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
				if artwork[0].startswith('MD'):
					wd.add(( URIRef( artworkURI ), RDFS.comment, Literal('artwork', datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

		# S_SUBJ_7
		people = getValuesFromFields("S_SUBJ_7-", recordData)
		if people:
			for person in people:
				personURI = getRightURIbase(person[0])+person[0]
				wd.add(( URIRef( collectionURI ), WDP.P921, URIRef( personURI ) ))
				wd.add(( URIRef( collectionURI ), URIRef( base+'hasSubjectPeople'), URIRef( personURI ) ))
				wd.add(( URIRef( personURI ), RDFS.label, Literal(person[1], datatype="http://www.w3.org/2001/XMLSchema#string" ) ))
				if person[0].startswith('MD'):
					wd.add(( URIRef( personURI ), RDFS.comment, Literal('person or organization', datatype="http://www.w3.org/2001/XMLSchema#string" ) ))

	# Create a copy in folder /records
	wd.serialize(destination='records/'+recordID+'.trig', format='trig', encoding='utf-8')
	# Load to the triplestore
	server.update('load <file:///'+dir_path+'/records/'+recordID+'.trig>')
