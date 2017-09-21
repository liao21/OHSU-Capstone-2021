import struct
import numpy

# one function, takes a string of bytes 
# e.g. from numpy.array.tobytes()
def extract(packet):
	
	# global constants
	PERCEPT_DATA = 200
	NONE = 0
	ALL_DOM_POS_VEL_TORQUE = 1
	ROC_TABLE_POS_VAL = 1
	CONTACT_FORCE_ACCEL_TEMP = 1
	CONTACT_FORCEv2_ACCEL_TEMP = 2
	NUM_JOINTS = 27
	PERCEPTS_PER_JOINT = 4
	
	# endianness in the struct.unpack function is controlled by a < or >
	endian = ">"
	
	# first two bytes are length as uint16
	packetLength = struct.unpack("H", packet[0:2])[0]
	
	# next byte is the streaming ID of the message
	MplStreamingMessageId = struct.unpack("B", packet[2])[0]
	ind = 0
	
	# this is the return value
	feedbackData = dict();
	
	# if this is a PERCEPT_DATA packet
	if MplStreamingMessageId == PERCEPT_DATA:
		ind = 3;
		
		# next byte is a limb percepts type, NONE is only supported option
		LimbPerceptsType = struct.unpack("B", packet[ind])[0]
		if LimbPerceptsType == NONE:
			ind += 1
		else:
			print("Warning: invalid LimbPerceptsType", LimbPerceptsType)
		
		# next byte is a joint percepts type
		JointPerceptsType = struct.unpack("B", packet[ind])[0]
		feedbackData["jointPercepts"] = dict()
		
		# fill in default values
		if JointPerceptsType == NONE:
			feedbackData["jointPercepts"]["position"] = [0 for i in range(NUM_JOINTS)]
			feedbackData["jointPercepts"]["velocity"] = [0 for i in range(NUM_JOINTS)]
			feedbackData["jointPercepts"]["torque"] = [0 for i in range(NUM_JOINTS)]
			feedbackData["jointPercepts"]["temperature"] = [0 for i in range(NUM_JOINTS)]
			ind += 1
		
		# parse next set of bytes into position, velocity, torque, temperature
		elif JointPerceptsType == ALL_DOM_POS_VEL_TORQUE:
			numFloats = PERCEPTS_PER_JOINT * NUM_JOINTS
			ind += 1
			temp = struct.unpack(endian + 'f' * numFloats, packet[ind:(ind+4*numFloats)])
			feedbackData["jointPercepts"]["position"] = temp[:NUM_JOINTS]
			feedbackData["jointPercepts"]["velocity"] = temp[NUM_JOINTS:NUM_JOINTS*2]
			feedbackData["jointPercepts"]["torque"] = temp[NUM_JOINTS*2:NUM_JOINTS*3]
			feedbackData["jointPercepts"]["temperature"] = temp[NUM_JOINTS*3:NUM_JOINTS*4]
			ind += 4 * numFloats
		
		# TODO: elevate something more formal?
		else:
			print("Warning: invalid JointPerceptsType", JointPerceptsType)
		
		# next set of bytes is a ROC percepts type.  this is untested at the moment
		ROCPerceptsType = struct.unpack("B", packet[ind])[0]
		ind += 1
		if ROCPerceptsType == NONE:
			pass
		elif ROCPerceptsType == ROC_TABLE_POS_VAL:
			
			# first parse the number of ROC tables
			numRocTables = struct.unpack("H", packet[ind])
			ind += 1
			
			# initialize key, value in return dict
			SIZE_OF_ROC_TABLE = 14; # num bytes
			NUM_ELEMENTS_IN_ROC_TABLE = 5;
			feedbackData["rocs"] = numpy.zeros((numRocTables, NUM_ELEMENTS_IN_ROC_TABLE))
			
			# parse all the ROC tables, one at a time
			for tableInd in range(numRocTables):
				# RocTablePosValType:
				#   uint8 rocTableid
				#   uint8 indexMode
				#   float index
				#   float value
				#   float weight
				feedbackData["rocs"][tableInd+1,:] = struct.unpack(endian + "BBfff")
				ind += SIZE_OF_ROC_TABLE
		
		# TODO: elevate something more formal?
		else:
			print("Warning: invalid ROCPerceptsType", ROCPerceptsType)
		
		# next byte is a segment percepts type
		SegmentPerceptsType = struct.unpack("B", packet[ind])[0]
		ind += 1
		
		# initialize segmentPercepts key/value in the return dict
		feedbackData["segmentPercepts"] = dict()
		
		# default: everything in segmentPercepts stays empty
		if SegmentPerceptsType == NONE:
			pass
			
		# todo: this seems inconsistent with the above pre-declaration
		elif SegmentPerceptsType == CONTACT_FORCE_ACCEL_TEMP:
			
			# constants for var dec
			NUM_CONTACT_SENSORS = 37;
			NUM_FTSN_SEGMENTS = 5; #index, middle, ring, little, thumb
			NUM_FTSN_DATA_MAX_NUMBER_VALUES = 3;
			
			# unpack next bytes as uint16's
			feedbackData["segmentPercepts"]["contactPercepts"] = struct.unpack(endian + "H" * NUM_CONTACT_SENSORS, packet[ind:(ind+NUM_CONTACT_SENSORS*2)])
			ind += NUM_CONTACT_SENSORS*2
			
			# pre-allocate ftsn dicts
			feedbackData["segmentPercepts"]["ftsnForce"]= numpy.zeros((NUM_FTSN_DATA_MAX_NUMBER_VALUES,NUM_FTSN_SEGMENTS))
			feedbackData["segmentPercepts"]["ftsnAccel"]= numpy.zeros((NUM_FTSN_DATA_MAX_NUMBER_VALUES,NUM_FTSN_SEGMENTS))
			feedbackData["segmentPercepts"]["ftsnTemp"]= numpy.zeros((NUM_FTSN_DATA_MAX_NUMBER_VALUES,NUM_FTSN_SEGMENTS))
			
			# fill in force vals
			for segmentId in range(NUM_FTSN_SEGMENTS):
				for axisId in range(NUM_FTSN_DATA_MAX_NUMBER_VALUES):
					force_temp = struct.unpack(endian + "f", packet[ind:ind+4])[0]
					ind += 4
					feedbackData["segmentPercepts"]["ftsnForce"][axisId, segmentId] = force_temp
			
			# fill in accel vals
			for segmentId in range(NUM_FTSN_SEGMENTS):
				for axisId in range(NUM_FTSN_DATA_MAX_NUMBER_VALUES):
					accel_temp = struct.unpack(endian + "f", packet[ind:ind+4])[0]
					ind += 4
					feedbackData["segmentPercepts"]["ftsnAccel"][axisId, segmentId] = accel_temp
			
			# fill in temp vals
			for segmentId in range(NUM_FTSN_SEGMENTS):
				for axisId in range(NUM_FTSN_DATA_MAX_NUMBER_VALUES):
					temp_temp = struct.unpack(endian + "f", packet[ind:ind+4])[0]
					ind += 4
					feedbackData["segmentPercepts"]["ftsnTemp"][axisId, segmentId] = temp_temp
		
		# extract the segment percepts, this is the current mode in use
		elif SegmentPerceptsType == CONTACT_FORCEv2_ACCEL_TEMP:
			
			# constants for variable declaration
			NUM_CONTACT_SENSORS = 37;
			NUM_FTSN_SEGMENTS = 5; #index, middle, ring, little, thumb
			NUM_FTSN_FORCE_MAX_NUMBER_VALUES = 14; # 14 capacitive force sensors
			NUM_FTSN_ACCEL_MAX_NUMBER_VALUES = 3; # 3 axes for force and acceleration data (only 1 for temperature)
						
			# fill in contact percepts
			# TODO: bytes aren't swapped in MATLAB, should be though?
			feedbackData["segmentPercepts"]["contactPercepts"] = struct.unpack("H" * NUM_CONTACT_SENSORS, packet[ind:(ind+NUM_CONTACT_SENSORS*2)])
			ind += NUM_CONTACT_SENSORS*2
			
			# pre-allocate ftsn dicts
			feedbackData["segmentPercepts"]["ftsnForce"]= numpy.zeros((NUM_FTSN_FORCE_MAX_NUMBER_VALUES,NUM_FTSN_SEGMENTS))
			feedbackData["segmentPercepts"]["ftsnAccel"]= numpy.zeros((NUM_FTSN_ACCEL_MAX_NUMBER_VALUES,NUM_FTSN_SEGMENTS))
			feedbackData["segmentPercepts"]["ftsnTemp"]= numpy.zeros((NUM_FTSN_SEGMENTS,))
			
			# fill in FTSN force vals
			for segmentId in range(NUM_FTSN_SEGMENTS):
				ind += 1
				for axisId in range(NUM_FTSN_FORCE_MAX_NUMBER_VALUES):
					force_temp = struct.unpack(endian + "f", packet[ind:ind+4])[0]
					ind += 4
					feedbackData["segmentPercepts"]["ftsnForce"][axisId, segmentId] = force_temp
			
			# fill in FTSN force vals
			for segmentId in range(NUM_FTSN_SEGMENTS):
				for axisId in range(NUM_FTSN_ACCEL_MAX_NUMBER_VALUES):
					accel_temp = struct.unpack(endian + "f", packet[ind:ind+4])[0]
					ind += 4
					feedbackData["segmentPercepts"]["ftsnAccel"][axisId, segmentId] = accel_temp
			
			# fill in FTSN force vals
			for segmentId in range(NUM_FTSN_SEGMENTS):
					temp_temp = struct.unpack(endian + "f", packet[ind:ind+4])[0]
					ind += 4
					feedbackData["segmentPercepts"]["ftsnTemp"][segmentId] = temp_temp
					
		# TODO: elevate something more formal?
		else:
			print("Warning: invalid SegmentPerceptsType", SegmentPerceptsType)
	
	# TODO: elevate something more formal?
	else:
		print("Warning: invalid MplStreamingMessageId", MplStreamingMessageId)

	
	# double-check that we parsed something
	if ind != 0:
		checksum = struct.unpack("B", packet[ind])[0]
	
	# otherwise, print warning
	# TODO: elevate something more formal?
	else:
		checksum = 0
		print("Warning: ind is 0, packet not parsed!")
	
	# double-check checksum
	# TODO: elevate something more formal?
	if checksum != sum(struct.unpack("B" * (len(packet)-1), packet[:-1])) % 256:
		print("Warning: invalid checksum in MPL percepts message")
	
	# verify that the value for ind is consistent with the stated length of the packet
	# TODO: elevate something more formal?
	if ind != (packetLength + 1):
		print("Warning: invalid packet length in message", packetLength, ind)
		
	return feedbackData
			