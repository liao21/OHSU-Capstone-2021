// global handle to websocket for send / receive commands
var socket;

jQuery(function($){

//Parse Query Strings for server information
// E.g. http://10.0.2.15:9090/?server=10.0.2.15

function getQueryVariable(variable)
{
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i=0;i<vars.length;i++) {
           var pair = vars[i].split("=");
           if(pair[0] == variable){return pair[1];}
    }
    return(false);
}  //getQueryVariable

// First check if server name provided, otherwise use the document's hostname, finally default to localhost
var server = getQueryVariable("server");
if (server == false){
    // Get document hostname
    server = document.location.hostname;
    if (server) {
        console.log(server)
    } else {
        console.log('Server name is Invalid')
        server = 'localhost'
    }
}

var host = "ws://" + server + ":9090/ws";
console.log(host)

if (!("WebSocket" in window)) {
alert("Your browser does not support web sockets");
}else{
setupWebsockets();
}

// Add query string &debug=1 to disable offline check
// E.g.: index.html?debug=1
var run = function(){
if (Offline.state === 'up' && getQueryVariable("debug") != "1")
    Offline.check();
}
setInterval(run, 3000);

// On html reconnect, reload websockets
Offline.on('up',setupWebsockets);



function setupWebsockets(){

// Note: You have to change the host var
// if your client runs on a different machine than the websocket server
socket = new WebSocket(host);

console.log("socket status: " + socket.readyState);

var $txt = $("#data");
var $btnSend = $("#sendtext");

$txt.focus();

// event handlers for UI
$btnSend.on('click',function(){
  var text = $txt.val();
  if(text == ""){
    return;
  }
  socket.send(text);
  $txt.val("");
});

$txt.keypress(function(evt){
  if(evt.which == 13){
    $btnSend.click();
  }
});

// event handlers for websocket
if(socket){

  socket.onopen = function(){
    //alert("connection opened....");
  }

  socket.onmessage = function(msg){
    //console.log(msg.data)

    value = msg.data;

 console.log("[onStringMessage] new message received ", value);
 var split_id = value.indexOf(":")
 var cmd_type = value.slice(0,split_id);
 var cmd_data = value.slice(split_id+1);

 if (cmd_type == "strStatus") {
     $("#msg_status").html(cmd_data);
     $("#msg_status_opt").html(cmd_data);
     $("#msg_status_myo").html(cmd_data);
 }
 if (cmd_type == "strTrainingMotion") {
     $("#msg_train").text(cmd_data);
 }
 if (cmd_type == "strOutputMotion") {
     $("#main_output").text(cmd_data);
     $("#mt_output").text(cmd_data);
     $("#tac_output").text(cmd_data);
 }
 if (cmd_type == "strMotionTester") {
     $("#mt_status").text(cmd_data);
 }
 if (cmd_type == "strMotionTesterProgress") {
     updateMTProgressBar(cmd_data);
 }
 if (cmd_type == "strMotionTesterImage") {
     updateMTImage(cmd_data);
 }
 if (cmd_type == "strTAC") {
     $("#tac_status").text(cmd_data);
 }
 if (cmd_type == "strTACJoint1Name") {
     $("#tacJoint1Name").text(cmd_data);
 }
 if (cmd_type == "strTACJoint1Bar") {
     updateTACJointBar(cmd_data, "tacJoint1Bar", "tacJoint1Label");
 }
 if (cmd_type == "strTACJoint1Target") {
    updateTACJointTarget(cmd_data, "tacJoint1Target");
 }
 if (cmd_type == "strTACJoint1Error") {
    updateTACJointError(cmd_data, "tacJoint1Target");
 }
 if (cmd_type == "strTACJoint2Name") {
     $("#tacJoint2Name").text(cmd_data);
 }
 if (cmd_type == "strTACJoint2Bar") {
     updateTACJointBar(cmd_data, "tacJoint2Bar", "tacJoint2Label");
 }
 if (cmd_type == "strTACJoint2Target") {
    updateTACJointTarget(cmd_data, "tacJoint2Target");
 }
 if (cmd_type == "strTACJoint2Error") {
    updateTACJointError(cmd_data, "tacJoint2Target");
 }
 if (cmd_type == "strTACJoint3Name") {
     $("#tacJoint3Name").text(cmd_data);
 }
 if (cmd_type == "strTACJoint3Bar") {
     updateTACJointBar(cmd_data, "tacJoint3Bar", "tacJoint3Label");
 }
 if (cmd_type == "strTACJoint3Target") {
    updateTACJointTarget(cmd_data, "tacJoint3Target");
 }
 if (cmd_type == "strTACJoint3Error") {
    updateTACJointError(cmd_data, "tacJoint3Target");
 }

}

  socket.onclose = function(){
    //alert("connection closed....");
    console.log("The connection has been closed.");
    socket.close
  }

}else{
  console.log("invalid socket");
}

setupCallbacks()
}

});  // jQuery

function setupCallbacks() {
    // listen to button clicks
    $("#ID_ADD").on("mousedown", function() {sendCmd("Cmd:Add")} );  // 4/5/2017 RSA: Moved to slider switch
    $("#ID_STOP").on("mousedown", function() {sendCmd("Cmd:Stop")} );  // 4/5/2017 RSA: Moved to slider switch
    $("#ID_CLEARCLASS").on("mousedown", function() {sendCmd("Cmd:ClearClass")} );
    $("#ID_CLEARALL").on("mousedown", function() {sendCmd("Cmd:ClearAll")} );
    $("#ID_TRAIN").on("mousedown", function() {sendCmd("Cmd:Train")} );
    $("#ID_SAVE").on("mousedown", function() {sendCmd("Cmd:Save")} );
    $("#ID_BACKUP").on("mousedown", function() {sendCmd("Cmd:Backup")} );
    $("#ID_SPEEDUP").on("mousedown", function() {sendCmd("Cmd:SpeedUp")} );
    $("#ID_SPEEDDOWN").on("mousedown", function() {sendCmd("Cmd:SpeedDown")} );
    $("#ID_HAND_SPEED_UP").on("mousedown", function() {sendCmd("Cmd:HandSpeedUp")} );
    $("#ID_HAND_SPEED_DOWN").on("mousedown", function() {sendCmd("Cmd:HandSpeedDown")} );
    /*$("#ID_PAUSE").on("mousedown", function() {sendCmd("Cmd:Pause")} );  // 4/5/2017 RSA: Moved to slider switch */
    $("#ID_PAUSE_HAND").on("mousedown", function() {sendCmd("Cmd:PauseHand")} );  // 4/5/2017 RSA: Moved to slider switch
    $("#ID_MYO1").on("mousedown", function() {sendCmd("Cmd:RestartMyo1")} );
    $("#ID_MYO2").on("mousedown", function() {sendCmd("Cmd:RestartMyo2")} );
    $("#ID_SELECT_MYO_SET_1").on("mousedown", function() {sendCmd("Cmd:ChangeMyoSet1")} );
    $("#ID_SELECT_MYO_SET_2").on("mousedown", function() {sendCmd("Cmd:ChangeMyoSet2")} );
    $("#ID_RELOAD_ROC").on("mousedown", function() {sendCmd("Cmd:ReloadRoc")} );
    $("#ID_REBOOT").on("mousedown", function() {sendCmd("Cmd:Reboot")} );
    $("#ID_SHUTDOWN").on("mousedown", function() {sendCmd("Cmd:Shutdown")} );
    $("#ID_ASSESSMENT_MT").on("mousedown", function() {startMT()} );
    $("#ID_ASSESSMENT_TAC1").on("mousedown", function() {startTAC1()} );
    $("#ID_ASSESSMENT_TAC3").on("mousedown", function() {startTAC3()} );
    $("#ID_GOTO_HOME").on("mousedown", function() {sendCmd("Cmd:GotoHome")} );
    $("#ID_GOTO_PARK").on("mousedown", function() {sendCmd("Cmd:GotoPark")} );

    // Create switch listeners:
    $('#trainSwitch').on("change", function() {
        if (this.checked) {
            sendCmd("Cmd:Add");
        } else {
            sendCmd("Cmd:Stop");
        }
    });
    $('#precisionMode').on("change", function() {
        if (this.checked) {
            sendCmd("Cmd:PrecisionModeOn");
        } else {
            sendCmd("Cmd:PrecisionModeOff");
        }
    });
    $('#pauseAll').on("change", function() {
        if (this.checked) {
            sendCmd("Cmd:PauseAllOn");
        } else {
            sendCmd("Cmd:PauseAllOff");
        }
    });
    $('#pauseHand').on("change", function() {
        if (this.checked) {
            sendCmd("Cmd:PauseHandOn");
        } else {
            sendCmd("Cmd:PauseHandOff");
        }
    });
    $('#resetTorque').on("change", function() {
        var val = this.value;
        if (val=="On") {
            sendCmd("Cmd:ResetTorqueOn");
        } else {
            sendCmd("Cmd:ResetTorqueOff");
        }
    });
    $('#enableImpedance').on("change", function() {
        var val = this.value;
        if (val=="On") {
            sendCmd("Cmd:ImpedanceOn");
        } else {
            sendCmd("Cmd:ImpedanceOff");
        }
    });
    $('#impedanceLevel').on("change", function() {
        var val = this.value;
        if (val=="Low") {
            sendCmd("Cmd:ImpedanceLow");
        } else {
            sendCmd("Cmd:ImpedanceHigh");
        }
    });
    $('#autoSave').on("change", function() {
        var val = this.value;
        if (val=="On") {
            sendCmd("Cmd:AutoSaveOn");
        } else {
            sendCmd("Cmd:AutoSaveOff");
        }
    });
    

}

// global sendCmd function called from index.html and galleryLinks.js
function sendCmd(cmd) {
    console.log("SEND:" + cmd);
    socket.send(cmd);
}

// submitLogMessage called from index.html 
function submitLogMessage() {
    var x = document.getElementById("ID_LOG_MSG").value;
    console.log('Logging ' + x);
    sendCmd("Log:" + x);
}

function startMT() {
// Gather parameters to send to motion tester
var repetitions = $("#ID_MT_REPETITIONS").val()
var timeout = $("#ID_MT_TIMEOUT").val()
var max_classifications = $("#ID_MT_MAX_CLASSIFICATIONS").val()
sendCmd("Cmd:StartMotionTester-" + repetitions + "-" + timeout + "-" + max_classifications)
}

function startTAC1() {
    // Gather parameters to send to TAC1
    var repetitions = $("#ID_REPETITIONS").val()
    var timeout = $("#ID_TIMEOUT").val()
    var dwell_time = $("#ID_DWELL_TIME").val()
    var degree_error = $("#ID_DEGREE_ERROR").val()
    var grasp_error = $("#ID_GRASP_ERROR").val()
    sendCmd("Cmd:StartTAC1-" + repetitions + "-" + timeout + "-" + dwell_time + "-" + degree_error + "-" + grasp_error)
}

function startTAC3() {
    // Gather parameters to send to TAC3
    var repetitions = $("#ID_REPETITIONS").val()
    var timeout = $("#ID_TIMEOUT").val()
    var dwell_time = $("#ID_DWELL_TIME").val()
    var degree_error = $("#ID_DEGREE_ERROR").val()
    var grasp_error = $("#ID_GRASP_ERROR").val()
    sendCmd("Cmd:StartTAC3-" + repetitions + "-" + timeout + "-" + dwell_time + "-" + degree_error + "-" + grasp_error)
}

// Function to update the motion tester progress bar based on user input
// See http://www.w3schools.com/howto/howto_js_progressbar.asp for details
function updateMTProgressBar(percent) {
    var elem = document.getElementById("mtProgressBar");
    elem.style.width = percent + '%';
    document.getElementById("mtProgressLabel").innerHTML = percent * 1  + '%';
}

// Function to update motion tester image based on class being assessed
function updateMTImage(imageFile){
    document.getElementById("ID_MT_IMAGE").src=imageFile
}

function updateTACJointBar(value, barId, labelId) {
    var elem = document.getElementById(barId);
    elem.style.marginLeft = value - 2.5 + '%'; // The 2.5 is to account for 5% width
    document.getElementById(labelId).innerHTML = Math.round(value * 1);
}

function updateTACJointError(value, elementId) {
    var elem = document.getElementById(elementId);
    elem.style.width = value*2 + '%'
}

function updateTACJointTarget(value, elementId) {
    var elem = document.getElementById(elementId);
    percentChar = elem.style.width
    percentNum  = percentChar.substring(0, percentChar.length - 1) // Remove percent sign
    halfWidth = percentNum * 1 / 2
    valuePercent = value * 1
    newMargin = valuePercent  - halfWidth
    newMarginPercent = newMargin * 1 + '%'
    elem.style.marginLeft = newMarginPercent;
}
