#recieves commands from web interface and creates a list of class instances with each selected feature

import pattern_rec as pr
import logging
import threading
import time
from utilities.user_config import read_user_config, set_user_config_var, get_user_config_var

class Features_selected(object):

    def __init__(self, vie):

        self.vie = vie
        self.create_instance_list()

    def command_string(self, value):
        """
        Commands are strings with the following format:

        [CMD_TYPE]:[CMD_VALUE]

        [CMD_TYPE] options are:
            Cmd - Indicates the cmd_value is a command word. Options are:
                mavOn
                mavOff
                curve_lenOn
                curve_lenOff
                zcOn
                zcOff
                sscOn
                sscOff
                wampOn
                wampOff
                varOn
                varOff
                vorderOn
                vorderOff
                logdetectOn
                logdetectOff
                emghistOn
                emghistOff
                arOn
                arOff
                cepsOn
                cepsOff
        """

        parsed = value.split(':')
        if not len(parsed) == 2:
            return
        else:
            cmd_type = parsed[0]
            cmd_data = parsed[1]

        if cmd_type == 'Cmd':
            if 'mavOn' in cmd_data:
                set_user_config_var("mav","True")
            elif 'mavOff' in cmd_data:
                set_user_config_var("mav","False")
            elif 'curve_lenOn' in cmd_data:
                set_user_config_var("curve_len","True")
            elif 'curve_lenOff' in cmd_data:
                set_user_config_var("curve_len","False")
            elif 'zcOn' in cmd_data:
                set_user_config_var("zc","True")
            elif 'zcOff' in cmd_data:
                set_user_config_var("zc","False")
            elif 'sscOn' in cmd_data:
                set_user_config_var("ssc","True")
            elif 'sscOff' in cmd_data:
                set_user_config_var("ssc","False")
            elif 'wampOn' in cmd_data:
                set_user_config_var("wamp","True")
            elif 'wampOff' in cmd_data:
                set_user_config_var("wamp","False")
            elif 'varOn' in cmd_data:
                set_user_config_var("var","True")
            elif 'varOff' in cmd_data:
                set_user_config_var("var","False")
            elif 'vorderOn' in cmd_data:
                set_user_config_var("vorder","True")
            elif 'vorderOff' in cmd_data:
                set_user_config_var("vorder","False")
            elif 'logdetectOn' in cmd_data:
                set_user_config_var("logdetect","True")
            elif 'logdetectOff' in cmd_data:
                set_user_config_var("logdetect","False")
            elif 'emghistOn' in cmd_data:
                set_user_config_var("emghist","True")
            elif 'emghistOff' in cmd_data:
                set_user_config_var("emghist","False")
            elif 'arOn' in cmd_data:
                set_user_config_var("ar","True")
            elif 'arOff' in cmd_data:
                set_user_config_var("ar","False")
            elif 'cepsOn' in cmd_data:
                set_user_config_var("ceps","True")
            elif 'cepsOff' in cmd_data:
                set_user_config_var("ceps","False")

            self.create_instance_list()

    def create_instance_list(self):

        self.vie.FeatureExtract.clear_features()

        if get_user_config_var("mav", "False") == "True":
            mav = pr.features.Mav()
            self.vie.FeatureExtract.attachFeature(mav)

        if get_user_config_var("curve_len", "False") == "True":
            curve_len = pr.features.Curve_len()
            self.vie.FeatureExtract.attachFeature(curve_len)

        if get_user_config_var("zc", "False") == "True":
            zc = pr.features.Zc()
            self.vie.FeatureExtract.attachFeature(zc)

        if get_user_config_var("ssc", "False") == "True":
            ssc = pr.features.Ssc()
            self.vie.FeatureExtract.attachFeature(ssc)

        if get_user_config_var("wamp", "False") == "True":
            wamp = pr.features.Wamp()
            self.vie.FeatureExtract.attachFeature(wamp)

        if get_user_config_var("var", "False") == "True":
            var = pr.features.Var()
            self.vie.FeatureExtract.attachFeature(var)

        if get_user_config_var("vorder", "False") == "True":
            vorder = pr.features.Vorder()
            self.vie.FeatureExtract.attachFeature(vorder)

        if get_user_config_var("logdetect", "False") == "True":
            logdetect = pr.features.Logdetect()
            self.vie.FeatureExtract.attachFeature(logdetect)

        if get_user_config_var("emghist", "False") == "True":
            emghist = pr.features.EMGhist()
            self.vie.FeatureExtract.attachFeature(emghist)

        if get_user_config_var("ar", "False") == "True":
            ar = pr.features.AR()
            self.vie.FeatureExtract.attachFeature(ar)

        if get_user_config_var("ceps", "False") == "True":
            ceps = pr.features.Ceps()
            self.vie.FeatureExtract.attachFeature(ceps)



