#recieves commands from web interface and creates a list of class instances with each selected feature

import pattern_rec as pr
from pattern_rec import features
import logging
import threading
import time
import utilities.user_config as uc

class Features_selected(object):

    def __init__(self,vie):

        self.vie = vie

    def create_instance_list(self):

        if uc.get_user_config_var("mav", "False") == "True":
            mav = features.Mav()
            self.vie.attachFeature(mav)

        if uc.get_user_config_var("curve_len", "False") == "True":
            curve_len = features.Curve_len(fs=uc.get_user_config_var('FeatureExtract.sample_rate', 200))
            self.vie.attachFeature(curve_len)

        if uc.get_user_config_var("zc", "False") == "True":
            zc = features.Zc(fs=uc.get_user_config_var('FeatureExtract.sample_rate', 200), zc_thresh=uc.get_user_config_var('FeatureExtract.zcThreshold', 0.05))
            self.vie.attachFeature(zc)

        if uc.get_user_config_var("ssc", "False") == "True":
            ssc = features.Ssc(fs=uc.get_user_config_var('FeatureExtract.sample_rate', 200), ssc_thresh=uc.get_user_config_var('FeatureExtract.zc_threshold', 0.05))
            self.vie.attachFeature(ssc)

        if uc.get_user_config_var("wamp", "False") == "True":
            wamp = features.Wamp(fs=uc.get_user_config_var('FeatureExtract.sample_rate', 200), wamp_thresh=uc.get_user_config_var('FeatureExtract.wamp_threshold', 0.05))
            self.vie.attachFeature(wamp)

        if uc.get_user_config_var("var", "False") == "True":
            var = features.Var()
            self.vie.attachFeature(var)

        if uc.get_user_config_var("vorder", "False") == "True":
            vorder = features.Vorder()
            self.vie.attachFeature(vorder)

        if uc.get_user_config_var("logdetect", "False") == "True":
            logdetect = features.Logdetect()
            self.vie.attachFeature(logdetect)

        if uc.get_user_config_var("emghist", "False") == "True":
            emghist = features.EMGhist()
            self.vie.attachFeature(emghist)

        if uc.get_user_config_var("ar", "False") == "True":
            ar = features.AR()
            self.vie.attachFeature(ar)

        if uc.get_user_config_var("ceps", "False") == "True":
            ceps = features.Ceps()
            self.vie.attachFeature(ceps)



