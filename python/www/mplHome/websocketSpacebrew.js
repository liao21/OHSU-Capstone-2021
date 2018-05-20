// websocketSpacebrew.js contains websocket messaging calls for Spacebrew
//
// Revisions:
//  24FEB2018 Armiger - Modularized for spacebrew communications

// Spacebrew Object
var sb, app_name = "MPL Control";

// when page loads call spacebrew setup function
$(window).on("load", setupSpacebrew);

/**
 * setupSpacebrew Function that creates and configures the connection to the Spacebrew server.
 *      It is called when the page loads.
 */
function setupSpacebrew() {
    var random_id = "0000" + Math.floor(Math.random() * 10000);

    app_name = app_name + ' ' + random_id.substring(random_id.length - 4);

    console.log("Setting up spacebrew connection");
    sb = new Spacebrew.Client("127.0.0.1");

    sb.name(app_name);
    sb.description("JHU/APL Mobile Training Interface");

    // configure the publication and subscription feeds
    sb.addPublish("cmdString", "string", "");
    sb.addSubscribe("statusString", "string");

    // connect to Spacebrew
    sb.connect();

    // override Spacebrew events - this is how you catch events coming from Spacebrew
    sb.onStringMessage = onStringMessage;
    sb.onOpen = onOpen;


} // setupSpacebrew

// global sendCmd function called from index.html and galleryLinks.js
function sendCmd(cmd) {
    if (sb) {
        console.log('Send ' + cmd);
        sb.send("cmdString", "string", cmd);
    }
}

/**
 * onStringMessage Function that is called whenever new spacebrew string messages are received.
 *          It accepts two parameters:
 * @param  {String} name    Holds name of the subscription feed channel
 * @param  {String} value 	Holds value received from the subscription feed
 */
function onStringMessage( name, value ){
  console.log("[onStringMessage] string message received ", value);
  var split_id = value.indexOf(":")
  var cmd_type = value.slice(0,split_id);
  var cmd_data = value.slice(split_id+1);
  routeMessage(cmd_type, cmd_data)
}

// Function that is called when Spacebrew connection is established
function onOpen() {
    console.log('Spacebrew Connected');
    var message = "Connected as <strong>" + sb.name() + "</strong>";
    if (sb.name() === app_name) {
        message += "<br>You can customize this app's name in the query string by adding <strong>name=your_app_name</strong>."
    }
    $("#statusMsg").html(message);

    // Perform browser based date synchronization
    console.log('Websockets are ready')
    var today = new Date();
    // getTime() always uses UTC for time representation. For example, a client browser in one timezone,
    // getTime() will be the same as a client browser in any other timezone.

    var delayInMilliseconds = 500;

    setTimeout(function() {
      //code executed after delay time
      sendCmd('Time:' + today.getTime())
    }, delayInMilliseconds);

}
