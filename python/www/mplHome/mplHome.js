// mplHome.js contains all the javascript for messaging between the mobile app webpage and the MPL Python VIE
// Websockets are used for communications so that status messages etc can be streamed from python to webpage
//
// Revisions:
//  28DEC2017 Armiger - Created initial revision and removed prior spacebrew implementation


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

  } else {
    console.log("invalid socket");
  }

  setupCallbacks()
} // setupWebsockets

function sendCmd(cmd) {
  // global sendCmd function called from index.html and galleryLinks.js
  console.log("SEND:" + cmd);
  socket.send(cmd);
}  // sendCmd

function routeMessage(cmd_type, cmd_data) {
  // Route the message to the appropriate section of the html page
  // based on the cmd_type.  Pass the target function the cmd_data

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

  // route joint percept message
  if (cmd_type == "jointCmd") {
    var values = cmd_data.split(',');
    $("#SHFE_Cmd").html(values[0]);
    $("#SHAA_Cmd").html(values[1]);
    $("#HUM_Cmd").html(values[2]);
    $("#EL_Cmd").html(values[3]);
    $("#WRT_Cmd").html(values[4]);
    $("#WAA_Cmd").html(values[5]);
    $("#WFE_Cmd").html(values[6]);
    $("#1AA_Cmd").html(values[7]);
    $("#1MCP_Cmd").html(values[8]);
    $("#1PIP_Cmd").html(values[9]);
    $("#1DIP_Cmd").html(values[10]);
    $("#2AA_Cmd").html(values[11]);
    $("#2MCP_Cmd").html(values[12]);
    $("#2PIP_Cmd").html(values[13]);
    $("#2DIP_Cmd").html(values[14]);
    $("#3AA_Cmd").html(values[15]);
    $("#3MCP_Cmd").html(values[16]);
    $("#3PIP_Cmd").html(values[17]);
    $("#3DIP_Cmd").html(values[18]);
    $("#4AA_Cmd").html(values[19]);
    $("#4MCP_Cmd").html(values[20]);
    $("#4PIP_Cmd").html(values[21]);
    $("#4DIP_Cmd").html(values[22]);
    $("#5AA_Cmd").html(values[23]);
    $("#5CMC_Cmd").html(values[24]);
    $("#5MCP_Cmd").html(values[25]);
    $("#5DIP_Cmd").html(values[26]);
  }
  if (cmd_type == "jointPos") {
    var values = cmd_data.split(',');
    $("#SHFE_Pos").html(values[0]);
    $("#SHAA_Pos").html(values[1]);
    $("#HUM_Pos").html(values[2]);
    $("#EL_Pos").html(values[3]);
    $("#WRT_Pos").html(values[4]);
    $("#WAA_Pos").html(values[5]);
    $("#WFE_Pos").html(values[6]);
    $("#1AA_Pos").html(values[7]);
    $("#1MCP_Pos").html(values[8]);
    $("#1PIP_Pos").html(values[9]);
    $("#1DIP_Pos").html(values[10]);
    $("#2AA_Pos").html(values[11]);
    $("#2MCP_Pos").html(values[12]);
    $("#2PIP_Pos").html(values[13]);
    $("#2DIP_Pos").html(values[14]);
    $("#3AA_Pos").html(values[15]);
    $("#3MCP_Pos").html(values[16]);
    $("#3PIP_Pos").html(values[17]);
    $("#3DIP_Pos").html(values[18]);
    $("#4AA_Pos").html(values[19]);
    $("#4MCP_Pos").html(values[20]);
    $("#4PIP_Pos").html(values[21]);
    $("#4DIP_Pos").html(values[22]);
    $("#5AA_Pos").html(values[23]);
    $("#5CMC_Pos").html(values[24]);
    $("#5MCP_Pos").html(values[25]);
    $("#5DIP_Pos").html(values[26]);
  }
  if (cmd_type == "jointTorque") {
    var values = cmd_data.split(',');
    $("#SHFE_Torque").html(values[0]);
    $("#SHAA_Torque").html(values[1]);
    $("#HUM_Torque").html(values[2]);
    $("#EL_Torque").html(values[3]);
    $("#WRT_Torque").html(values[4]);
    $("#WAA_Torque").html(values[5]);
    $("#WFE_Torque").html(values[6]);
    $("#1AA_Torque").html(values[7]);
    $("#1MCP_Torque").html(values[8]);
    $("#1PIP_Torque").html(values[9]);
    $("#1DIP_Torque").html(values[10]);
    $("#2AA_Torque").html(values[11]);
    $("#2MCP_Torque").html(values[12]);
    $("#2PIP_Torque").html(values[13]);
    $("#2DIP_Torque").html(values[14]);
    $("#3AA_Torque").html(values[15]);
    $("#3MCP_Torque").html(values[16]);
    $("#3PIP_Torque").html(values[17]);
    $("#3DIP_Torque").html(values[18]);
    $("#4AA_Torque").html(values[19]);
    $("#4MCP_Torque").html(values[20]);
    $("#4PIP_Torque").html(values[21]);
    $("#4DIP_Torque").html(values[22]);
    $("#5AA_Torque").html(values[23]);
    $("#5CMC_Torque").html(values[24]);
    $("#5MCP_Torque").html(values[25]);
    $("#5DIP_Torque").html(values[26]);
  }
  if (cmd_type == "jointTemp") {
    var values = cmd_data.split(',');
    $("#SHFE_Temp").html(values[0]);
    $("#SHAA_Temp").html(values[1]);
    $("#HUM_Temp").html(values[2]);
    $("#EL_Temp").html(values[3]);
    $("#WRT_Temp").html(values[4]);
    $("#WAA_Temp").html(values[5]);
    $("#WFE_Temp").html(values[6]);
    $("#1AA_Temp").html(values[7]);
    $("#1MCP_Temp").html(values[8]);
    $("#1PIP_Temp").html(values[9]);
    $("#1DIP_Temp").html(values[10]);
    $("#2AA_Temp").html(values[11]);
    $("#2MCP_Temp").html(values[12]);
    $("#2PIP_Temp").html(values[13]);
    $("#2DIP_Temp").html(values[14]);
    $("#3AA_Temp").html(values[15]);
    $("#3MCP_Temp").html(values[16]);
    $("#3PIP_Temp").html(values[17]);
    $("#3DIP_Temp").html(values[18]);
    $("#4AA_Temp").html(values[19]);
    $("#4MCP_Temp").html(values[20]);
    $("#4PIP_Temp").html(values[21]);
    $("#4DIP_Temp").html(values[22]);
    $("#5AA_Temp").html(values[23]);
    $("#5CMC_Temp").html(values[24]);
    $("#5MCP_Temp").html(values[25]);
    $("#5DIP_Temp").html(values[26]);
  }

}  // routeMessage

function setupCallbacks() {
  // Create callback listeners for commands generated from html

  // Create button click based listeners:
  $("#ID_CLEARCLASS").on("mousedown", function() {sendCmd("Cmd:ClearClass")} );
  $("#ID_CLEARALL").on("mousedown", function() {sendCmd("Cmd:ClearAll")} );
  $("#ID_TRAIN").on("mousedown", function() {sendCmd("Cmd:Train")} );
  $("#ID_SAVE").on("mousedown", function() {sendCmd("Cmd:Save")} );
  $("#ID_BACKUP").on("mousedown", function() {sendCmd("Cmd:Backup")} );
  $("#ID_SPEEDUP").on("mousedown", function() {sendCmd("Cmd:SpeedUp")} );
  $("#ID_SPEEDDOWN").on("mousedown", function() {sendCmd("Cmd:SpeedDown")} );
  $("#ID_HAND_SPEED_UP").on("mousedown", function() {sendCmd("Cmd:HandSpeedUp")} );
  $("#ID_HAND_SPEED_DOWN").on("mousedown", function() {sendCmd("Cmd:HandSpeedDown")} );
  $("#ID_MYO1").on("mousedown", function() {sendCmd("Cmd:RestartMyo1")} );
  $("#ID_MYO2").on("mousedown", function() {sendCmd("Cmd:RestartMyo2")} );
  $("#ID_SELECT_MYO_SET_1").on("mousedown", function() {sendCmd("Cmd:ChangeMyoSet1")} );
  $("#ID_SELECT_MYO_SET_2").on("mousedown", function() {sendCmd("Cmd:ChangeMyoSet2")} );
  $("#ID_RELOAD_ROC").on("mousedown", function() {sendCmd("Cmd:ReloadRoc")} );
  $("#ID_REBOOT").on("mousedown", function() {sendCmd("Cmd:Reboot")} );
  $("#ID_SHUTDOWN").on("mousedown", function() {sendCmd("Cmd:Shutdown")} );
  $("#ID_ASSESSMENT_MT").on("mousedown", function() {startMT()} );
  $("#ID_ASSESSMENT_MT_STOP").on("mousedown", function() {stopMT()} );
  $("#ID_ASSESSMENT_TAC1").on("mousedown", function() {startTAC1()} );
  $("#ID_ASSESSMENT_TAC3").on("mousedown", function() {startTAC3()} );
  $("#ID_ASSESSMENT_TAC_STOP").on("mousedown", function() {stopTAC()} );
  $("#ID_GOTO_HOME").on("mousedown", function() {sendCmd("Cmd:GotoHome")} );
  $("#ID_GOTO_PARK").on("mousedown", function() {sendCmd("Cmd:GotoPark")} );

  $("#MAN_ElbowFlex").on("mousedown", function() {sendCmd("Man:Elbow Flexion")} );
  $("#MAN_ElbowExtend").on("mousedown", function() {sendCmd("Man:Elbow Extension")} );
  $("#MAN_Pronate").on("mousedown", function() {sendCmd("Man:Wrist Rotate In")} );
  $("#MAN_Supinate").on("mousedown", function() {sendCmd("Man:Wrist Rotate Out")} );
  $("#MAN_WristFlex").on("mousedown", function() {sendCmd("Man:Wrist Flex In")} );
  $("#MAN_WristExtend").on("mousedown", function() {sendCmd("Man:Wrist Extend Out")} );
  $("#MAN_HandOpen1").on("mousedown", function() {sendCmd("Man:Hand Open")} );
  $("#MAN_HandOpen2").on("mousedown", function() {sendCmd("Man:Hand Open")} );
  $("#MAN_Spherical").on("mousedown", function() {sendCmd("Man:Spherical Grasp")} );
  $("#MAN_Tip").on("mousedown", function() {sendCmd("Man:Tip Grasp")} );
  $("#MAN_ThreeFingerPinch").on("mousedown", function() {sendCmd("Man:Three Finger Pinch Grasp")} );
  $("#MAN_Lateral").on("mousedown", function() {sendCmd("Man:Lateral Grasp")} );
  $("#MAN_Cylindrical").on("mousedown", function() {sendCmd("Man:Cylindrical Grasp")} );
  $("#MAN_Point").on("mousedown", function() {sendCmd("Man:Point Grasp")} );
  $("#MAN_Index").on("mousedown", function() {sendCmd("Man:Index")} );
  $("#MAN_Middle").on("mousedown", function() {sendCmd("Man:Middle")} );
  $("#MAN_Ring").on("mousedown", function() {sendCmd("Man:Ring")} );
  $("#MAN_Little").on("mousedown", function() {sendCmd("Man:Little")} );
  $("#MAN_Thumb").on("mousedown", function() {sendCmd("Man:Thumb")} );
  $("#MAN_RingMiddle").on("mousedown", function() {sendCmd("Man:Ring-Middle")} );
  $("#MAN_TheBird").on("mousedown", function() {sendCmd("Man:The Bird")} );
  $("#MAN_Stop1").on("mousedown", function() {sendCmd("Man:Stop")} );
  $("#MAN_Stop2").on("mousedown", function() {sendCmd("Man:Stop")} );


  // Create checkbox based switch listeners:
  $('#trainSwitch').on("change", function() { this.checked === true ? sendCmd("Cmd:Add") : sendCmd("Cmd:Stop"); });
  $('#precisionMode').on("change", function() { this.checked === true ? sendCmd("Cmd:PrecisionModeOn") : sendCmd("Cmd:PrecisionModeOff"); });
  $('#pauseAll').on("change", function() { this.checked === true ? sendCmd("Cmd:PauseAllOn") : sendCmd("Cmd:PauseAllOff"); });
  $('#pauseHand').on("change", function() { this.checked === true ? sendCmd("Cmd:PauseHandOn") : sendCmd("Cmd:PauseHandOff"); });

  // Create slider based switch listeners:
  $('#resetTorque').on("change", function() { this.value == "On" ? sendCmd("Cmd:ResetTorqueOn") : sendCmd("Cmd:ResetTorqueOff"); });
  $('#enableImpedance').on("change", function() { this.value == "On" ? sendCmd("Cmd:ImpedanceOn") : sendCmd("Cmd:ImpedanceOff"); });
  $('#impedanceLevel').on("change", function() { this.value == "Low" ? sendCmd("Cmd:ImpedanceLow") : sendCmd("Cmd:ImpedanceHigh"); });
  $('#autoSave').on("change", function() { this.value == "On" ? sendCmd("Cmd:AutoSaveOn") : sendCmd("Cmd:AutoSaveOff"); });
  $('#autoOpen').on("change", function() { this.value == "On" ? sendCmd("Cmd:AutoOpenOn") : sendCmd("Cmd:AutoOpenOff"); });

  $('#manualControl').on("change", function() { this.value == "On" ? sendCmd("Cmd:ManualControlOn") : sendCmd("Cmd:ManualControlOff"); });
  $('#streamPercepts').on("change", function() { this.value == "On" ? sendCmd("Cmd:JointPerceptsOn") : sendCmd("Cmd:JointPerceptsOff"); });
}  // setupCallbacks

function submitLogMessage() {
  // submitLogMessage called from index.html
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

function stopMT() {
  sendCmd("Cmd:StopMotionTester")
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

function stopTAC() {
  sendCmd("Cmd:StopTAC")
}

function updateMTProgressBar(percent) {
  // Function to update the motion tester progress bar based on user input
  // See http://www.w3schools.com/howto/howto_js_progressbar.asp for details
  var elem = document.getElementById("mtProgressBar");
  elem.style.width = percent + '%';
  document.getElementById("mtProgressLabel").innerHTML = percent * 1  + '%';
}

function updateMTImage(imageFile){
  // Function to update motion tester image based on class being assessed
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
