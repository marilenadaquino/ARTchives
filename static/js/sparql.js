var yasqe = YASQE(document.getElementById("yasqe"), {
	sparql: {
		showQueryButton: true,
		endpoint: "http://localhost:8888/sparql",
		requestMethod: "GET"
	}
});

// TODO change endpoint

var yasr = YASR(document.getElementById("yasr"), {
	//this way, the URLs in the results are prettified using the defined prefixes in the query
	getUsedPrefixes: yasqe.getPrefixesFromQuery
});

//link both together
yasqe.setValue("")
yasqe.options.sparql.callbacks.complete = yasr.setResponse;