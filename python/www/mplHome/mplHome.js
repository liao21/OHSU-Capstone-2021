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

    // override Spacebrew events - this is how you catch events coming from Spacebrew
    sb.onStringMessage = onStringMessage;
    sb.onOpen = onOpen;

    // connect to Spacebrew
    sb.connect();

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
    $("#ID_PAUSE").on("mousedown", function() {sendCmd("Cmd:Pause")} );  // 4/5/2017 RSA: Moved to slider switch
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
    $('#autoSave').on("change", function() {
        var val = this.value;
        if (val=="On") {
            sendCmd("Cmd:AutoSaveOn");
        } else {
            sendCmd("Cmd:AutoSaveOff");
        }
    });
    

} // setupSpacebrew

// global sendCmd function called from index.html and galleryLinks.js
function sendCmd(cmd) {
    if (sb) {
        console.log('Send ' + cmd);
        sb.send("cmdString", "string", cmd);
    }
}

// submitLogMessage called from index.html 
function submitLogMessage() {
    if (sb) {
        var x = document.getElementById("ID_LOG_MSG").value;
        console.log('Logging ' + x);
        sendCmd("Log:" + x);
    }
}

// Function that is called when Spacebrew connection is established
function onOpen() {
    console.log('Spacebrew Connected');
    var message = "Connected as <strong>" + sb.name() + "</strong>";
    if (sb.name() === app_name) {
        message += "<br>You can customize this app's name in the query string by adding <strong>name=your_app_name</strong>."
    }
    $("#statusMsg").html(message);
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

     if (name == "statusString") {
         if (cmd_type == "strStatus") {
             $("#msg_status").html(cmd_data);
             $("#msg_status2").html(cmd_data);
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
