/**
 * Example code to send CloudWatch Log to a Sumo hosted HTTP collector
 * 
 * You are free to use and redistribute.  No warranty is implied by the author or anyone else.
 * 
 * All you need to do is upating the hostname and the path in the options
 */
 
var zlib = require('zlib');
var https = require('https');
var options = {
    hostname: 'collectors.us2.sumologic.com',
    port: 443,
    path: '//receiver/v1/http/ZaVnC4dhaV1_rBXh3egE8XKXVC80uTqPpr22fyOLQKNlcxUWLMkJZqS8-11sYovNiogaqYuECH9K2zVYa9kJDu1D8Dlk5M0DN6eYQHmZRU3m-wlljz55NA==',
    method: 'POST',
    headers: {
      'Content-Type':'application/json',
      'Content-Length': 0
    }
};
var buf=new Buffer('');

exports.handler = function(event, context) {
    var payload = new Buffer(event.awslogs.data, 'base64');
    zlib.gunzip(payload, function(e, result) {
            if (e) {
                context.fail(e);
            } else {
                result = JSON.parse(result.toString('ascii'));
                console.log("Received " + result.logEvents.length + " log events.");
                for(var i in result.logEvents) {
                   buf +=JSON.stringify(result.logEvents[i])+"\n";
		}
            	options.headers['Content-Length']=buf.length;
            	var body = '';
                var request = https.request(options, function(response) {
                	console.log('STATUS: ' + response.statusCode);
                  	if (response.statusCode != 200) {
                      		context.fail();
                  	} else {
            			response.on('data', function(chunk) {
                			body += chunk;
            			});
            			response.on('end', function() {
                			console.log('Successfully processed HTTPS response');
					context.succeed();
            			});  
                	}
                });
                request.write(buf);
                request.end()
            }
        })
};
