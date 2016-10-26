from enum import IntEnum


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
