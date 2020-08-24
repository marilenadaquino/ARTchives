# -*- coding: utf-8 -*-
import web , datetime , os, time, re, cgi, requests
from urllib.parse import parse_qs
import forms, mapping, conf, queries
from web import form
web.config.debug = False
prefix = ''
#prefixLocal = '/artchives/'
prefixLocal = ''

urls = (
	prefix + '/', 'Login',
	prefix + '/logout', 'Logout',
	prefix + '/welcome','Index',
	prefix + '/record-(.+)', 'Record',
	prefix + '/modify-(.+)', 'Modify',
	prefix + '/review-(.+)', 'Review',
	prefix + '/about', 'About',
	prefix + '/credits', 'Credits',
	prefix + '/contribute', 'Contribute',
	prefix + '/documentation', 'Documentation',
	prefix + '/historians', 'Historians',
	prefix + '/historian-(.+)', 'Historian',
	prefix + '/collections', 'Collections',
	prefix + '/collection-(.+)', 'Collection',
	prefix + '/institutions', 'Keepers',
	prefix + '/keeper-(.+)', 'Keeper',
	prefix + '/(sparql)','sparql',
	prefix + '/bibliography','Bibliography',
)


app = web.application(urls, globals())

if web.config.get('_session') is None:
	store = web.session.DiskStore('sessions')
	session = web.session.Session(app, store, initializer={'logged_in': 'False', 'username': 'anonymous', 'password': 'None'})
	web.config._session = session
	session_data = session._initializer
else:
	session = web.config._session
	session_data = session._initializer

render = web.template.render('templates/', base="layout", cache=False, globals={'session':session, 'clean':mapping.clean_to_uri})
render2 = web.template.render('templates/', globals={'session':session})
render_no_login = web.template.render('templates/', base="layout_no_login", globals={'session':session})

# TODO Hash passw
allowed = (

)

def notfound():
    return web.notfound(render.notfound(user='anonymous'))

def internalerror():
    return web.internalerror(render.internalerror(user='anonymous'))

app.notfound = notfound
app.internalerror = internalerror

class Notfound:
    def GET(self):
        raise web.notfound()

def logout(page):
	"""default behaviour for logout"""
	data = web.input()
	login = data.login
	passwd = data.passwd
	if(login,passwd) in allowed:
		session['logged_in'] = True
		session['username'] = login
		session['password'] = passwd
		print(datetime.datetime.now(),'LOGIN:', session['username'])
		raise web.seeother(prefixLocal+'welcome')
	else:
		return render.page(user='anonymous')



class Login:
	def GET(self):
		if(session.username,session.password) in allowed:
			session.logged_in = True
			raise web.seeother(prefixLocal+'welcome')
		else:
			return render.login(user='anonymous')

	def POST(self):
		data = web.input()
		login = data.login
		passwd = data.passwd
		if(login,passwd) in allowed:
			session['logged_in'] = True
			session['username'] = login
			session['password'] = passwd
			print(datetime.datetime.now(),'LOGIN:', session['username'])
			raise web.seeother(prefixLocal+'welcome')
		else:
			return render.login(user='anonymous')

wikidir = os.path.realpath('./records/') 

class Logout:
	def GET(self):
		session['logged_in'] = 'False'
		session['username'] = 'anonymous'
		print(datetime.datetime.now(),'LOGOUT:', session['username'])
		return render.login(user='anonymous')

	def POST(self):
		logout(prefixLocal)


class Index:
	def GET(self):
		web.header("Content-Type","text/html; charset=utf-8")
		web.header('Access-Control-Allow-Origin', '*')
		web.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
		if (session['username'],session['password']) in allowed:
			session['logged_in'] = 'True'
			userID = session['username'].replace('@','-at-').replace('.','-dot-')
			records = reversed(sorted(queries.getRecords(), key=lambda tup: tup[4]))
			#records = queries.getRecords() # get all the records
			return render.index(wikilist=records, user=session['username'], varIDpage=userID+'-record-'+str(time.time()).replace('.','-') )
		else:
			session['logged_in'] = 'False'
			return render.login(user='anonymous')

	def POST(self):
		actions = web.input()
		web.header("Content-Type","text/html; charset=utf-8")
		web.header('Access-Control-Allow-Origin', '*')
		web.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
		# create a new record
		if actions.action.startswith('createRecord'):
			record = 'record-'+actions.action.split("createRecord",1)[1]
			print(datetime.datetime.now(),'START NEW RECORD:', actions.action.split("createRecord",1)[1], session['username'])
			raise web.seeother(prefixLocal+record)
		# delete a record (but not the dump in /records folder)
		elif actions.action.startswith('deleteRecord'):
			record = actions.action.split("deleteRecord",1)[1]
			queries.deleteRecord(record)
			userID = session['username'].replace('@','-at-').replace('.','-dot-')
			#records = queries.getRecords() # get all the records
			records = reversed(sorted(queries.getRecords(), key=lambda tup: tup[4]))
			print(datetime.datetime.now(),'DELETED RECORD:', record, session['username'])
			return render.index(wikilist=records, user=session['username'], varIDpage=userID+'-record-'+str(time.time()).replace('.','-') )
		# modify a record
		elif actions.action.startswith('modify'):
			record = 'record-'+actions.action.split("artchives/",1)[1].replace('/','')
			print(datetime.datetime.now(),'MODIFY RECORD:', actions.action.split("artchives/",1)[1].replace('/',''), session['username'])
			raise web.seeother(prefixLocal+'modify-'+record)
		# start review
		elif actions.action.startswith('review'):
			record = 'record-'+actions.action.split("artchives/",1)[1].replace('/','')
			if session['username'] == "marilena.daquino2@unibo.it":
				print(datetime.datetime.now(),'START REVIEW RECORD:', actions.action.split("artchives/",1)[1].replace('/',''), session['username'])
				raise web.seeother(prefixLocal+'review-'+record)
			else:
				raise web.seeother(prefixLocal+'welcome')


class Record(object):
	def GET(self, name):
		web.header("Cache-Control", "no-cache, max-age=0, must-revalidate, no-store")
		web.header("Content-Type","text/html; charset=utf-8")
		web.header('Access-Control-Allow-Origin', '*')
		web.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
		if (session['username'],session['password']) in allowed:
			session['logged_in'] = 'True'
			f = forms.art_historian()
			print(session_data,'\n',session['username'],f.S_COLL_2.render())
			return render.record(record_form=f, pageID=name, user=session['username'])
		else:
			session['logged_in'] = 'False'
			return render.login(user=session['username'])

	def POST(self, name):
		web.header("Content-Type","text/html; charset=utf-8")
		web.header('Access-Control-Allow-Origin', '*')
		web.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
		f = forms.art_historian()
		if not f.validates():
			return render.record(record_form=f, pageID=name, user=session['username'])
		else:
			recordData = web.input()
			recordID = recordData.recordID
			#userID = recordID.split("-record-",1)[0]
			userID = session['username'].replace('@','-at-').replace('.','-dot-')
			mapping.artchivesToWD(recordData, userID, 'not modified')
			# TODO empty recordData
			# TODO quick statement to wd
			print(datetime.datetime.now(),'CREATED RECORD:', recordID, session['username'])
			raise web.seeother(prefixLocal+'welcome')


class Modify(object):
	def GET(self, name):
		web.header("Cache-Control", "no-cache, max-age=0, must-revalidate, no-store")
		web.header("Content-Type","text/html; charset=utf-8")
		web.header('Access-Control-Allow-Origin', '*')
		web.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
		if (session['username'],session['password']) in allowed:
			session_data['logged_in'] = 'True'
			graphToRebuild = mapping.base+name.split("record-",1)[1]+'/'
			recordID = name
			data = queries.getData(graphToRebuild)
			print(session_data,'\n',session['username'])
			f = forms.art_historian()
			return render.modify(graphdata=data, pageID=recordID, record_form=f, user=session['username']) # render the form filled
		else:
			session['logged_in'] = 'False'
			return render.login(user='anonymous')

	# TODO validate form!
	def POST(self, name):
		web.header("Content-Type","text/html; charset=utf-8")
		web.header('Access-Control-Allow-Origin', '*')
		web.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
		recordData = web.input()
		recordID = recordData.recordID
		# userID = recordID.rsplit("-record-",2)[1]
		userID = session['username'].replace('@','-at-').replace('.','-dot-')
		graphToClear = mapping.base+recordID.split("record-",1)[1]+'/'

		mapping.artchivesToWD(recordData, userID, 'modified', graphToClear)
		print(datetime.datetime.now(),'MODIFIED RECORD:', recordID, session['username'])
		raise web.seeother(prefixLocal+'welcome')


class Review(object):
	def GET(self, name):
		web.header("Cache-Control", "no-cache, max-age=0, must-revalidate, no-store")
		web.header("Content-Type","text/html; charset=utf-8")
		web.header('Access-Control-Allow-Origin', '*')
		web.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
		if session['username'] == "marilena.daquino2@unibo.it" or session['username'] == 'francesca.mambelli6@unibo.it':
			session['logged_in'] = 'True'
			graphToRebuild = mapping.base+name.split("record-",1)[1]+'/'
			recordID = name
			data = queries.getData(graphToRebuild)
			print(session_data,'\n',session['username'])
			f = forms.art_historian()
			return render.review(graphdata=data, pageID=recordID, record_form=f, graph=graphToRebuild, user=session['username']) # render the form filled
		else:
			raise web.seeother(prefixLocal+'welcome')

	def POST(self, name):
		web.header("Content-Type","text/html; charset=utf-8")
		web.header('Access-Control-Allow-Origin', '*')
		web.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
		actions = web.input()
		# save the new record for future publication
		if actions.action.startswith('save'):
			recordData = web.input()
			recordID = recordData.recordID
			userID = session['username'].replace('@','-at-').replace('.','-dot-')
			graphToClear = mapping.base+name.split("record-",1)[1]+'/'
			mapping.artchivesToWD(recordData, userID, 'modified',graphToClear)
			print(datetime.datetime.now(),'REVIEWED RECORD (NOT PUBLISHED YET):', recordID, session['username'])
			raise web.seeother(prefixLocal+'welcome')

		# publish
		if actions.action.startswith('publish'):
			record = 'record-'+actions.action.split("publishRecord",1)[1]
			recordData = web.input()
			recordID = recordData.recordID
			userID = session['username'].replace('@','-at-').replace('.','-dot-')
			graphToClear = mapping.base+name.split("record-",1)[1]+'/'
			mapping.artchivesToWD(recordData, userID, 'published',graphToClear)
			print(datetime.datetime.now(),'PUBLISHED RECORD:', recordID, session['username'])
			raise web.seeother(prefixLocal+'welcome')


class About:
	def GET(self):
		return render_no_login.about(user='anonymous')

	def POST(self):
		logout('about')

class Credits:
	def GET(self):
		return render_no_login.credits(user='anonymous')

	def POST(self):
		logout('credits')

class Bibliography:
	def GET(self):
		return render_no_login.bibliography(user='anonymous')

	def POST(self):
		logout('bibliography')

class Contribute:
	def GET(self):
		return render_no_login.contribute(user='anonymous')

	def POST(self):
		logout('contribute')

class Documentation:
	def GET(self):
		return render_no_login.documentation(user='anonymous')

	def POST(self):
		logout('documentation')

class Historians:
	def GET(self):
		records = queries.getHistorians()
		fh = forms.searchHistorian()
		return render_no_login.historians(form=fh, user='anonymous', data=records, title='Art historians')

	def POST(self):
		logout('historians')

class Historian(object):
	def GET(self, name):
		# TO BE CHANGED
		historianID = name
		print(name)
		historianURI = mapping.getRightURIbase(historianID)+historianID
		dataHistorian = queries.getHistorian(historianURI)
		print(historianURI)
		# TODO add other properties/links pIn and pOut
		return render_no_login.historian(user='anonymous', graphdata=dataHistorian, graphID=historianID)

	def POST(self):
		logout('historian')

class Collections:
	def GET(self):
		records = queries.getCollections()
		fc = forms.searchCollection()
		return render_no_login.collections(form=fc, user='anonymous', data=records, title='Collections')

	def POST(self):
		logout('collections')

class Collection(object):
	def GET(self, name):
		graphID = name
		graph = mapping.base+graphID+'/'
		dataCollection = queries.getData(graph)
		# TODO add other properties/links pIn and pOut
		return render_no_login.collection(user='anonymous', graphdata=dataCollection, graphID=graphID)

	def POST(self):
		logout('collection')

class Keepers:
	def GET(self):
		records = queries.getKeepers()
		fk = forms.searchKeeper()
		return render_no_login.keepers(form=fk, user='anonymous', data=records, title='Institutions')

	def POST(self):
		logout('keepers')

class Keeper(object):
	def GET(self, name):
		# TO BE CHANGED
		keeperID = name
		keeperURI = mapping.getRightURIbase(keeperID)+keeperID
		dataKeeper = queries.getKeeper(keeperURI)
		# TODO add other properties/links pIn and pOut
		return render_no_login.keeper(user='anonymous', graphdata=dataKeeper, graphID=keeperID)

	def POST(self):
		logout('keeper')

class sparql:
    def GET(self, active):
        content_type = web.ctx.env.get('CONTENT_TYPE')
        return self.__run_query_string(active, web.ctx.env.get("QUERY_STRING"), content_type)

    def POST(self, active):
        content_type = web.ctx.env.get('CONTENT_TYPE')
        web.debug("The content_type value: ")
        web.debug(content_type)

        cur_data = web.data()
        if "application/x-www-form-urlencoded" in content_type:
            print ("QUERY TO ENDPOINT:", cur_data)
            return self.__run_query_string(active, cur_data, True, content_type)
        elif "application/sparql-query" in content_type:
            print("QUERY TO ENDPOINT:", cur_data)
            return self.__contact_tp(cur_data, True, content_type)
        else:
            raise web.redirect("/sparql")

    def __contact_tp(self, data, is_post, content_type):
        accept = web.ctx.env.get('HTTP_ACCEPT')
        if accept is None or accept == "*/*" or accept == "":
            accept = "application/sparql-results+xml"
        if is_post:
            req = requests.post('http://artchives.fondazionezeri.unibo.it:3000/sparql', data=data,
                                headers={'content-type': content_type, "accept": accept})
        else:
            req = requests.get("%s?%s" % ('http://artchives.fondazionezeri.unibo.it:3000/sparql', data),
                               headers={'content-type': content_type, "accept": accept})

        if req.status_code == 200:
            web.header('Access-Control-Allow-Origin', '*')
            web.header('Access-Control-Allow-Credentials', 'true')
            web.header('Content-Type', req.headers["content-type"])

            return req.text
        else:
            raise web.HTTPError(
                str(req.status_code), {"Content-Type": req.headers["content-type"]}, req.text)

    def __run_query_string(self, active, query_string, is_post=False,
                           content_type="application/x-www-form-urlencoded"):
        parsed_query = parse_qs(query_string)
        if query_string is None or query_string.strip() == "":
            return render2.sparql(active, user='anonymous')
        if re.search("updates?", query_string, re.IGNORECASE) is None:
            if "query" in parsed_query:
                return self.__contact_tp(query_string, is_post, content_type)
            else:
                raise web.redirect(conf.artchivesPublicEndpoint)
        else:
            raise web.HTTPError(
                "403", {"Content-Type": "text/plain"}, "SPARQL Update queries are not permitted.")


if __name__ == "__main__":
	app.run()
