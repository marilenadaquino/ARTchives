# -*- coding: utf-8 -*-
import web , datetime , os, time, re, cgi
from web import form

vemail = form.regexp(r".*@.*", "must be a valid email address")
vphone = form.regexp(r"[0-9]+", "must be a valid phone number")
vsite = form.regexp(r"^http+", "must be a valid URL, e.g. http://example.com")
# add validators and required fields
# TODO validators for hidden fields!! aggiungi almeno 1 hidden con form.notnull e vedi se fa casino con il numero incrementale (o l'id di wd)
# REMEMBER no '-'' in the name/id
art_historian = form.Form(
	form.Textbox("S_KEEPER_title",  
    	description="Keeper", 
    	disabled="disabled", 
    	id="S_KEEPER_title"),
    form.Textbox("S_KEEPER_1", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Full name", 
    	autocomplete="off", 
    	id="S_KEEPER_1", 
    	placeholder="e.g. Fondazione Federico Zeri",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="The name of the keeper of the collection; e.g. Fondazione Zeri"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_KEEPER_2", 
    	class_="freeText col-md-11", 
    	description="Address",  
        autocomplete="off", 
    	id="S_KEEPER_2", 
    	placeholder="e.g. 2, Piazzetta Giorgio Morandi",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="The address of the keeper. House number first; e.g. 2, Piazzetta Giorgio Morandi"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_KEEPER_3", 
    	class_="searchWikidata col-md-11", 
    	description="City", 
    	autocomplete="off", 
    	id="S_KEEPER_3", 
    	placeholder="e.g. Bologna",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="The city or town of the keeper; e.g. Bologna"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_KEEPER_4", 
    	class_="searchWikidata col-md-11", 
    	description="District", 
    	autocomplete="off", 
    	id="S_KEEPER_4", 
    	placeholder="e.g. Province of Bologna",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="The district of the keeper; e.g. Province of Bologna"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_KEEPER_5", 
    	class_="searchWikidata col-md-11", 
    	description="Country", 
    	autocomplete="off", 
    	id="S_KEEPER_5", 
    	placeholder="e.g. Italy",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="The country of the keeper; e.g. Italy"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_KEEPER_6", 
    	class_="freeText col-md-11", 
    	description="Phone",  
        autocomplete="off", 
    	id="S_KEEPER_6", 
    	placeholder="e.g. 00390512097471",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Phone number, including national prefix of the keeper; e.g. 00390512097471"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_KEEPER_7", 
    	class_="freeText col-md-11", 
    	description="Email",  
        autocomplete="off", 
    	id="S_KEEPER_7", 
    	placeholder="e.g. fondazionezeri.info@unibo.it",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Email of the keeper; e.g. fondazionezeri.info@unibo.it"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_KEEPER_8", 
    	class_="freeText col-md-11", 
    	description="Website", 
        autocomplete="off",  
    	id="S_KEEPER_8", 
    	placeholder="e.g. http://www.fondazionezeri.unibo.it/en",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Website of the keeper (start with http://); e.g. http://www.fondazionezeri.unibo.it/en"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_CREATOR_title",  
    	description="Art historian", 
    	disabled="disabled", 
    	id="S_CREATOR_title"),
    form.Textbox("S_CREATOR_1", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Full name", 
    	autocomplete="off", 
    	id="S_CREATOR_1", 
    	placeholder="e.g. Everett Fahy",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Name of the art historian who created the collection; e.g. Everett Fahy"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_CREATOR_2", 
    	class_="freeText col-md-11", 
    	description="Dates",  
        autocomplete="off", 
    	id="S_CREATOR_2", 
    	placeholder="e.g. 1941-2018, 1941-, -2018",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Birth year and death year; e.g. 1941-2018, 1941-, -2018"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_CREATOR_3", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Profession", 
    	autocomplete="off", 
    	id="S_CREATOR_3", 
    	placeholder="e.g. museum director",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Role or profession of the art historian; e.g. museum director"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_CREATOR_4", 
    	class_="searchWikidata col-md-11", 
    	description="Country", 
    	autocomplete="off", 
    	id="S_CREATOR_4", 
    	placeholder="e.g. United States of America",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Country of the art historian\'s citizenship; e.g. United States of America"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textarea("S_CREATOR_5", 
    	class_="freeText col-md-11", 
    	description="Biography",  
        autocomplete="off", 
    	id="S_CREATOR_5", 
    	placeholder="e.g. Fahy was raised in Philadelphia, PA. While and undergraduate at the University of Virginia, Fahy met his future chair namesake, Sir John Pope-Hennessy...",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Short biography of the art historian; e.g. Fahy was raised in Philadelphia, PA. While and undergraduate at the University of Virginia, Fahy met his future chair namesake, Sir John Pope-Hennessy..."><i class="fas fa-info-circle"></i></span>' 	
        ),
    form.Textarea("S_CREATOR_6", 
    	class_="freeText col-md-11", 
    	description="Art historian's bibliography", 
    	id="S_CREATOR_6", 
    	autocomplete="off", 
    	placeholder="e.g. Fahy, E. (1976). Some Followers of Domenico Ghirlandajo. New York, NY: Garland.",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Main bibliographic references authored by the art historian. Cite a reference in APA citation style; e.g. Fahy, E. (1976). Some Followers of Domenico Ghirlandajo. New York, NY: Garland."><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textarea("S_CREATOR_7", 
    	class_="freeText col-md-11", 
    	description="Bibliography on the art historian", 
    	id="S_CREATOR_7", 
    	autocomplete="off", 
    	placeholder="e.g. Shirey, David L. (1973, May 20). Everett Fahy of the Met Is Named Frick Director. New York Times, p. 63.",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Main bibliographic references having as subject the art historian. Cite a reference in APA citation style; e.g. Shirey, David L. (1973, May 20). Everett Fahy of the Met Is Named Frick Director. New York Times, p. 63."><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_COLLECTION_title",  
    	description="Collection", 
    	disabled="disabled", 
    	id="S_COLLECTION_title"),
    form.Textbox("S_COLL_1", 
    	class_="freeText col-md-11", 
    	description="Reference code",  
        autocomplete="off", 
    	id="S_COLL_1", 
    	placeholder="e.g. FZ.2017.Fahy",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Code identifying the collection; e.g. FZ.2017.Fahy"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_COLL_2", 
    	class_="freeText col-md-11", 
    	description="Collection name", 
        autocomplete="off",  
    	id="S_COLL_2", 
    	placeholder="e.g. Fototeca Fahy",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Name of the collection or fond; e.g. Fototeca Fahy"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_COLL_3", 
    	class_="freeText col-md-11", 
    	description="Dates",  
        autocomplete="off", 
    	id="S_COLL_3", 
    	placeholder="e.g. 1965-2018, 1965-, -2018",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Date range of the collection or fond; e.g. 1965-2018, 1965-, -2018"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textarea("S_COLL_4", 
    	class_="freeText col-md-11", 
    	description="Extent and medium", 
        autocomplete="off",  
    	id="S_COLL_4", 
    	placeholder="e.g. 451 boxes",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Brief description of items included in the collection or fond; e.g. 451 boxes"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textarea("S_COLL_5", 
    	class_="freeText col-md-11", 
    	description="System of arrangement",  
        autocomplete="off", 
    	id="S_COLL_5", 
    	placeholder="e.g. Documents and photos in  boxes are grouped in folders, in alphabetical order.",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Internal structure, order and/or system of classification of the unit of description; e.g. Documents and photos in  boxes are grouped in folders, in topographical / chronological / alphabetical order. The order given by the art historian has been maintaned."><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_COLL_6", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Main type of objects", 
    	autocomplete="off", 
    	id="S_COLL_6", 
    	placeholder="e.g. photograph, archive document, book, compact disc, map, video",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Main type of collected documents (use the singular form); e.g. photograph, archive document, book, compact disc, map, video"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_COLL_7", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Other types of objects", 
    	autocomplete="off", 
    	id="S_COLL_7", 
    	placeholder="e.g. photograph, archive document, book, compact disc, map, video",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Other types of collected documents (use the singular form); e.g. photograph, archive document, book, compact disc, map, video"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textarea("S_COLL_8", 
    	class_="freeText col-md-11", 
    	description="Scope and content", 
        autocomplete="off",  
    	id="S_COLL_8", 
    	placeholder="e.g. The archive consists of some 85,000 items of which about 45,000 paper documents (including letters, typewritten lists, photocopies of articles, postcards, drafts and handwritten notes) and 39,800 photographs (especially gelatine silver prints, albumen prints and diacolors)...",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="List relevant themes, materials and archival series; e.g. The archive consists of some 85,000 items of which about 45,000 paper documents (including letters, typewritten lists, photocopies of articles, postcards, drafts and handwritten notes) and 39,800 photographs (especially gelatine silver prints, albumen prints and diacolors)..."><i class="fas fa-info-circle"></i></span>'
        ),
    form.Textarea("S_COLL_9", 
    	class_="freeText col-md-11", 
    	description="History of the collection", 
        autocomplete="off",  
    	id="S_COLL_9", 
    	placeholder="e.g. The origins of the archive apparently date back to the years of Fahy's university studies...",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Historical notes on the collection; e.g. The origins of archive should date back to the years of Fahy\'s university studies..."><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_COLL_10", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Type of acquisition", 
    	autocomplete="off", 
    	id="S_COLL_10", 
    	placeholder="e.g. loan, donation",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="e.g. loan, bequest"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_COLL_11", 
    	class_="freeText col-md-11", 
    	description="Year of acquisition",  
        autocomplete="off", 
    	id="S_COLL_11", 
    	placeholder="e.g. 2017",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Year of acquisition of the collection; e.g. 2017"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_COLL_12", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Repository", 
    	autocomplete="off", 
    	id="S_COLL_12", 
    	placeholder="e.g. Fondazione Zeri",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Repository or specific location; e.g. Fondazione Zeri"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textarea("S_COLL_13", 
    	class_="freeText col-md-11", 
    	description="Access", 
    	autocomplete="off", 
    	id="S_COLL_13", 
        placeholder="e.g. partially restricted (available by appointment)",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Specify whether the access to the collection is restricted, partially restricted or unrestricted"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_COLL_14", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Reproduction (licences)", 
    	autocomplete="off", 
    	id="S_COLL_14", 
    	placeholder="e.g. Creative Commons Attribution-NonCommercial-NoDerivatives",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Restrictions on reproduction. Specify a license, e.g. Creative Commons Attribution-NonCommercial-NoDerivatives"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textarea("S_COLL_15", 
    	class_="freeText col-md-11", 
    	description="Finding aids", 
        autocomplete="off",  
    	id="S_COLL_15", 
    	placeholder="e.g. Series level descriptions available with associated box lists...",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Information on finding aids; e.g. Series level descriptions available with associated box lists"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_COLL_16", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Cataloguing standard", 
    	autocomplete="off", 
    	id="S_COLL_16", 
    	placeholder="e.g. ISAD(G), ICCD-F",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Name of cataloguing or archival standard; e.g. ISAD(G)"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textarea("S_COLL_17", 
    	class_="freeText col-md-11", 
    	description="Bibliography", 
    	id="S_COLL_17", 
    	autocomplete="off", 
    	placeholder="e.g. Ottani Cavina, Anna (ed). (2011). La pittura italiana nella Fototeca Zeri. Fotografie scelte. Turin, Italy: Allemandi.",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Main bibliographic references on the collection. Cite a reference in APA citation style; e.g. Ottani Cavina, Anna (ed). (2011). La pittura italiana nella Fototeca Zeri. Fotografie scelte. Turin, Italy: Allemandi."><i class="fas fa-info-circle"></i></span>'
    	),

    form.Textbox("S_COLL_18_1", 
    	class_="freeText col-md-5", 
    	description="Online resources",  
        autocomplete="off", 
    	id="S_COLL_18_1", 
    	placeholder="",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="URL of web pages including the description of the fond or catalogues, records, etc. E.g. http://example.com"><i class="fas fa-info-circle"></i></span>'
    	),

    form.Textbox("S_COLL_18_1_desc", 
        class_="freeText col-md-5", 
        autocomplete="off",   
        id="S_COLL_18_1_desc", 
        placeholder="",
        pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Please include a brief description. E.g. online catalogue; inventory;"><i class="fas fa-info-circle"></i></span>'
        ),
    form.Textbox("S_COLL_18_2", 
        class_="freeText col-md-5", 
        autocomplete="off",  
        id="S_COLL_18_2", 
        placeholder="",
        pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="URL of web pages including the description of the fond or catalogues, records, etc. E.g. http://example.com"><i class="fas fa-info-circle"></i></span>'
        ),

    form.Textbox("S_COLL_18_2_desc", 
        class_="freeText col-md-5",  
        autocomplete="off",  
        id="S_COLL_18_2_desc", 
        placeholder="",
        pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Please include a brief description. E.g. online catalogue; inventory;"><i class="fas fa-info-circle"></i></span>'
        ),
    form.Textbox("S_COLL_18_3", 
        class_="freeText col-md-5", 
        autocomplete="off",   
        id="S_COLL_18_3", 
        placeholder="",
        pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="URL of web pages including the description of the fond or catalogues, records, etc. E.g. http://example.com"><i class="fas fa-info-circle"></i></span>'
        ),

    form.Textbox("S_COLL_18_3_desc", 
        class_="freeText col-md-5", 
        autocomplete="off",   
        id="S_COLL_18_3_desc", 
        placeholder="",
        pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Please include a brief description. E.g. online catalogue; inventory;"><i class="fas fa-info-circle"></i></span>'
        ),

    form.Textbox("S_COLL_19", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Aggregators", 
    	autocomplete="off", 
    	id="S_COLL_19", 
    	placeholder="e.g. Europeana, CulturaItalia",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Aggregators including the data collection (if applicable); e.g. Europeana, CulturaItalia"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_COLL_20", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Events", 
    	autocomplete="off", 
    	id="S_COLL_20", 
    	placeholder="e.g. Il patrimonio perduto nelle fotografie di Federico Zeri, 2014, Fondazione Zeri",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Events related to the collection, such as exhibitions. Record events in the form: Title, Year, Place. e.g. IL PATRIMONIO PERDUTO NELLE FOTOGRAFIE DI FEDERICO ZERI, 2014, Fondazione Zeri"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textarea("S_COLL_21", 
    	class_="freeText col-md-11", 
    	description="Notes",  
        autocomplete="off", 
    	id="S_COLL_21", 
    	placeholder="e.g. The collection is relevant for Renaissance studies...",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Notes on the scope or relevance of the collection, e.g. archivsts\' advise for researchers"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textarea("S_COLL_22", 
        class_="freeText col-md-11", 
        description="Notes on related nuclei",  
        autocomplete="off", 
        id="S_COLL_22", 
        placeholder="e.g. Photographs and letters available in Roberto Longhi's personal archive.",
        pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Notes on related nuclei of documents that are available in other collections. Please specify the name of the institution, the name of the collection, and the main type of objects available."><i class="fas fa-info-circle"></i></span>'
        ),
    form.Textbox("S_SUBJECT_title",  
    	description="Main subjects of the collection", 
    	disabled="disabled", 
    	id="S_SUBJECT_title"),
    form.Textbox("S_SUBJ_1", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Periods", 
    	autocomplete="off", 
    	id="S_SUBJ_1", 
    	placeholder="e.g. 17th century, Baroque",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Periods or artistic periods that are in scope in the collection. e.g. 17th century, Baroque"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_SUBJ_2", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Genres and themes", 
    	autocomplete="off", 
    	id="S_SUBJ_2", 
    	placeholder="e.g. Christian Iconography, Potrait, Mithology",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Genres and themes that are in scope in the collection. e.g. Christian Iconography, Potrait, Mithology"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_SUBJ_4", 
        class_="searchWikidata searchARTchives col-md-11", 
        description="Artists and schools", 
        autocomplete="off", 
        id="S_SUBJ_4", 
        placeholder="e.g. Apollonio di Giovanni, Sandro Botticelli, Leonardo da Vinci",
        pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Artists and artistic schools that are in scope in the collection. e.g. Apollonio di Giovanni, Sandro Botticelli, Leonardo da Vinci"><i class="fas fa-info-circle"></i></span>'
        ),
    form.Textbox("S_SUBJ_5", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Types of artwork", 
    	autocomplete="off", 
    	id="S_SUBJ_5", 
    	placeholder="e.g. painting, sculpture, drawing, altarpiece",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Types of artwork that are in scope in the collection. e.g. painting, sculpture, drawing, altarpiece"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_SUBJ_6", 
    	class_="searchWikidata searchARTchives col-md-11", 
    	description="Artworks", 
    	autocomplete="off", 
    	id="S_SUBJ_6", 
    	placeholder="e.g. Sistine Chapel, Roverella altarpiece",
    	pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Artworks and monuments that are in scope in the collection. e.g. Sistine Chapel, Roverella altarpiece"><i class="fas fa-info-circle"></i></span>'
    	),
    form.Textbox("S_SUBJ_7", 
        class_="searchWikidata searchARTchives col-md-11", 
        description="People and organizations (e.g. scholars, collectors, correspondents)", 
        autocomplete="off", 
        id="S_SUBJ_7", 
        placeholder="e.g. Federico Zeri, Roberto Longhi, Galleria Sangiorgi",
        pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="People and organizations (historians, museums, etc.) that are in scope in the collection"><i class="fas fa-info-circle"></i></span>'
        ),
)


# form.Textbox("S_SUBJ_3", 
#     class_="searchWikidata col-md-11", 
#     description="Places", 
#     autocomplete="off", 
#     id="S_SUBJ_3", 
#     placeholder="Search in Wikidata...select items from the list or press enter",
#     pre='<span class="tip" data-toggle="tooltip" data-placement="bottom" title="Places that are in scope in the collection. e.g. Florence, Siena"><i class="fas fa-info-circle"></i></span>'
#     ),

searchHistorian = form.Form(
	form.Textbox("search", 
    	class_="searchHistorian col-md-11", 
    	description="Search an art historian", 
    	autocomplete="off")
)

searchCollection = form.Form(
    form.Textbox("search", 
        class_="searchCollection col-md-11", 
        description="Search a collection", 
        autocomplete="off")
)

searchKeeper = form.Form(
    form.Textbox("search", 
        class_="searchKeeper col-md-11", 
        description="Search a keeper", 
        autocomplete="off")
)

#searchGeneral = form.Form(
    #form.Textbox("search", 
        #class_="searchGeneral", 
        #description="search", 
        #autocomplete="off")
#)


