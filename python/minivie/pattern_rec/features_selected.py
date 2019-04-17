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
            self.vie.attach_feature(mav)

        if uc.get_user_config_var("curve_len", "False") == "True":
            curve_len = features.CurveLen(fs=uc.get_user_config_var('FeatureExtract.sample_rate', 200))
            self.vie.attach_feature(curve_len)

        if uc.get_user_config_var("zc", "False") == "True":
            zc = features.Zc(fs=uc.get_user_config_var('FeatureExtract.sample_rate', 200), zc_thresh=uc.get_user_config_var('FeatureExtract.zcThreshold', 0.05))
            self.vie.attach_feature(zc)

        if uc.get_user_config_var("ssc", "False") == "True":
            ssc = features.Ssc(fs=uc.get_user_config_var('FeatureExtract.sample_rate', 200), ssc_thresh=uc.get_user_config_var('FeatureExtract.zc_threshold', 0.05))
            self.vie.attach_feature(ssc)

        if uc.get_user_config_var("wamp", "False") == "True":
            wamp = features.Wamp(fs=uc.get_user_config_var('FeatureExtract.sample_rate', 200), wamp_thresh=uc.get_user_config_var('FeatureExtract.wamp_threshold', 0.05))
            self.vie.attach_feature(wamp)

        if uc.get_user_config_var("var", "False") == "True":
            var = features.Var()
            self.vie.attach_feature(var)

        if uc.get_user_config_var("vorder", "False") == "True":
            vorder = features.Vorder()
            self.vie.attach_feature(vorder)

        if uc.get_user_config_var("logdetect", "False") == "True":
            logdetect = features.LogDetect()
            self.vie.attach_feature(logdetect)

        if uc.get_user_config_var("emghist", "False") == "True":
            emghist = features.EmgHist()
            self.vie.attach_feature(emghist)

        if uc.get_user_config_var("ar", "False") == "True":
            ar = features.AR()
            self.vie.attach_feature(ar)

        if uc.get_user_config_var("ceps", "False") == "True":
            ceps = features.Ceps()
            self.vie.attach_feature(ceps)



