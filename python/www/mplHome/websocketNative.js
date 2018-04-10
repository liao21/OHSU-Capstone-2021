// websocketNative.js contains websocket messaging calls
//
// Revisions:
//  24FEB2018 Armiger - Modularized for websocket only communications

// global handle to websocket for send / receive commands
var socket;

jQuery(function($){
  // function invoked when the document has been loaded and the DOM is ready to be manipulated

  if (!("WebSocket" in window)) {
    alert("Your browser does not support web sockets");
  } else {
    setupWebsockets();
  }

  // Setup Offline Monitor
  var run = function(){
  if (Offline.state === 'up')
    Offline.check();
  }
  setInterval(run, 3000);

  // On html reconnect, reload websockets
  Offline.on('up',setupWebsockets);

});  // jQuery

function setupWebsockets(){
  // Create websocket connection
  var host = "ws://" + document.location.hostname + ":" + document.location.port + "/ws";
  console.log(host)
  socket = new WebSocket(host);

  console.log("socket status: " + socket.readyState);

  // event handlers for websocket
  if(socket){
    socket.onmessage = function(msg){
      value = msg.data;
      console.log("[onStringMessage] new message received ", value);
      var split_id = value.indexOf(":")
      var cmd_type = value.slice(0,split_id);
      var cmd_data = value.slice(split_id+1);
      routeMessage(cmd_type, cmd_data)
    }  // socket.onmessage

    socket.onclose = function(){
      //alert("connection closed....");
      console.log("The connection has been closed.");
      socket.close
    }  //socket.onclose

    socket.onopen = function(){
    // Perform browser based date syncronization

      console.log('Websockets are ready')
      var today = new Date();
      console.log(today.getTime());
      console.log('Done')
      // getTime() always uses UTC for time representation. For example, a client browser in one timezone,
      // getTime() will be the same as a client browser in any other timezone.
      sendCmd('Time:' + today.getTime())
    } //socket.onopen

  } else {
    console.log("Invalid socket");
  }

} // setupWebsockets

function sendCmd(cmd) {
  // global sendCmd function called from index.html and galleryLinks.js
  console.log("SEND:" + cmd);
  socket.send(cmd);
}  // sendCmd
