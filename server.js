var   app 
	, url = require('url')
    , io
	, sys = require('sys')
	, spawn = require('child_process').spawn
	, exec = require('child_process').exec
	, proc  // for spawn
	, child // for exec
	, connection = 0
	, max_connections = 5

function start_app(route, handle) {
	app = require('http').createServer(onRequest).listen(process.env.PORT || 8888)
	io = require('socket.io').listen(app, { log: false }).set('log level', 1)

	console.log(" . ONLINE ]-[ http://localhost:8888 .")

	function onRequest(request, response) {
		var pathname = url.parse(request.url).pathname.replace("/","")

		route(handle, pathname, request, response)
	}
	
	//START SOCKET IO
	io.sockets.on('connection', function (socket) {
		process_state = false
		if ( ++connection > (max_connections+1) ) {
			connection--
			return
		}
		// START DICONNECT EVENT
		socket.on('disconnect',function() {
  			connection = 0
			//proc.stdin.setEncoding = 'utf-8'
			//proc.stdin.write( "die" + "\n")
			exec("python3 reset.py")
			//if(proc != undefined)			
				proc.kill("SIGKILL")
		})
		// END DISCONNECT EVENT

		//////////////////////////////////////////////
		// START PULSE EVENTs
		// pulses are for programs that don't need input
		//socket.on('pulse', function(data){
		//	if(process_state) return
		//	child = exec(data.msg, function (err , stdout, stderr) {
		//		echoIO(stdout)
		//		if(stderr.length > 1) echoIO(stderr)
		//		if ( err ) console.log(' . sys err ' + stderr)
		//	})
		//})
		// END PULSE EVENT
		
		//////////////////////////////////////////////
		// START PROGRAM EVENT
		socket.on('proc_start', function(data){
			console.log(' . starting ' + data.proc_name)
			try {
				proc = spawn('apps/' + data.proc_name)
				var pid = proc.pid
				echoIO( pid )
				toggleState()
				processDriver(proc)
			}
			catch(e) {
				console.log(e)
				echoIO(' * error running executable')
			}
		})
		// START SCRIPT EVENT
		socket.on('script_start', function(script){
			console.log(' . starting ' + script.type + " " + script.name + " " + script.args )
			try {
				var type = script.type
					,name= 'apps/' + script.name
					,args= script.args
					,pid
				proc = spawn(type,[name],args)
				pid = proc.pid
				echoIO( pid )
				toggleState()
				processDriver(proc)
			}
			catch(e) {
				console.log(e)
				echoIO(' * error running executable')
			}
		})
		// KILL PROGRAM
		socket.on('proc_end', function() {
			try {
				//proc.kill("SIGKILL")
				//proc.stdin.setEncoding = 'utf-8'
				proc.stdin.write( "die" + '\n' )
				proc.stdin.end()			
			}
			catch(e)
			{
				console.log(" . kill err .")
			}
			toggleState("off")
		})
		// get message and forward to process
		socket.on('toProc', function(data) {
			console.log( " . sending: " + data.command )
			//var datum = data.command.replace(" ", "")
			proc.stdin.setEncoding = 'utf-8'
			proc.stdin.write( data.command + "\n")
			//proc.stdin.end()
		})
		// END PROGRAM EVENT

		// PROGRAM DRIVER
		// FORWARDING PROGRAM MESSAGES
		function processDriver(proc) {
			proc.stdout.setEncoding('utf-8');
			proc.stdout.on('data', function (data) {
				var res = data.toString()	
				//echoIO(res)
				//console.log( " . STDOUT " + res )			
				try {				
					sendProcState(JSON.parse(res))
				}
				catch(e) {
					echoIO(" * malformed process state")
				}
			})
			proc.stderr.on('data', function (data) {
				console.log( " . ERR " + data)
				var res = data.toString()
				echoIO(res)
			})

			proc.on('exit', function (code) {
				console.log( " . EXIT " +  code)
				stateOff()
				echoIO("exit " + code)
				sendProcState(JSON.parse('{"status":"not_running"}'))
			})
		}// END DRIVER

		//////////////////////////////////////////////
		// SOCKET IO METHODS
		function echoIO(s) {
			socket.emit('echo', s)		
		}
		function sendProcState(s)
		{
			socket.emit('execState', s)
		}
		// TOGGLE LOCK STATE
		function toggleState(s) {
			process_state = !process_state
			if(process_state || s == "on")
				stateOn()					
			else if(!process_state || s == "off")
				stateOff()
		}
		function stateOff() {
			socket.emit('state_change', "UNLOCK" )
			process_state = 0
		}
		function stateOn() {
			socket.emit('state_change', "LOCKED")
			process_state = 1
		}		
		// END TOGGLE LOCK STATE
	}) // END SOCKET IO	
}

exports.start_app = start_app;