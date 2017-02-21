from enum import IntEnum, unique

@unique
class JointEnum(IntEnum):
    """
        Allows enumeration reference for joint angles

        Example:

        JointEnum(1).name
        'SHOULDER_AB_AD'

    """
    SHOULDER_FE = 0
    SHOULDER_AB_AD = 1
    HUMERAL_ROT = 2
    ELBOW = 3
    WRIST_ROT = 4
    WRIST_AB_AD = 5
    WRIST_FE = 6
    INDEX_AB_AD = 7
    INDEX_MCP = 8
    INDEX_PIP = 9
    INDEX_DIP = 10
    MIDDLE_AB_AD = 11
    MIDDLE_MCP = 12
    MIDDLE_PIP = 13
    MIDDLE_DIP = 14
    RING_AB_AD = 15
    RING_MCP = 16
    RING_PIP = 17
    RING_DIP = 18
    LITTLE_AB_AD = 19
    LITTLE_MCP = 20
    LITTLE_PIP = 21
    LITTLE_DIP = 22
    THUMB_CMC_AB_AD = 23
    THUMB_CMC_FE = 24
    THUMB_MCP = 25
    THUMB_DIP = 26
    NUM_JOINTS = 27


@unique
class NfuUdpMsgId(IntEnum):
    """
        Enumerate NFU UDP Message Types

        This enum is defined in RP3-SD630-9930-ICD_MPL_UDP_ICD_RevB_20120731, Section 3.1.2.4, Table 3 - Messages

        Example:
            import mpl
            (mpl.NfuUdpMsgId.UDPMSGID_HEARTBEATV2 == 203)
                True

            str(mpl.NfuUdpMsgId(203)).split('.')[1]

                'UDPMSGID_HEARTBEATV2'

    """

    UDPMSGID_RESERVED = 0,
    UDPMSGID_WRITE_CONFIGVALUES = 1,
    UDPMSGID_READ_CONFIGVALUES = 2,
    UDPMSGID_PING_VULCANX = 3,
    UDPMSGID_RESET_CONFIGVALUES_DEFAULTS = 4,
    UDPMSGID_ACTUATEMPL = 5, # primary control method, used to send DOM, ROC, and EP motion commands
    UDPMSGID_WRITE_IMPEDANCEVALUES = 6,
    UDPMSGID_READ_MPLSTATUS = 7,
    UDPMSGID_WRITE_PERCEPTCONFIGURATION = 8,
    UDPMSGID_NFU_IDLE = 9,
    UDPMSGID_NFU_SOFTRESTART = 10,
    UDPMSGID_NACK = 100,
    UDPMSGID_PERCEPTDATA = 200,
    UDPMSGID_PERCEPTDATA_HANDONLY = 201,
    # UDPMSGID_HEARTBEATV1 is not packed with MUD headers, no message identifier is used
    UDPMSGID_HEARTBEATV2 = 203,
    UDPMSGID_MPLERROR = 210,


@unique
class LcSwState(IntEnum):
    SWSTATE_INIT						= 0,
    SWSTATE_PRG						    = 1,
    SWSTATE_FS							= 2,
    SWSTATE_NOS_CONTROL_STIMULATION	    = 3,
    SWSTATE_NOS_IDLE					= 4,
    SWSTATE_NOS_SLEEP					= 5,
    SWSTATE_NOS_CONFIGURATION			= 6,
    SWSTATE_NOS_HOMING                  = 7,
    SWSTATE_NOS_DATA_ACQUISITION        = 8,
    SWSTATE_NOS_DIAGNOSTICS             = 9,
    #SWSTATE_NUM_STATES					= 10
    SWSTATE_UNK                         = 15,
