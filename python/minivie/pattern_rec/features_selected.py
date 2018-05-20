#recieves commands from web interface and creates a list of class instances with each selected feature

import pattern_rec as pr
import logging
import threading
import time
import utilities.user_config as uc

class Features_selected(object):

    def __init__(self,vie):

        self.vie = vie

    def create_instance_list(self):

        if uc.get_user_config_var("mav", "False") == "True":
            mav = pr.features.Mav()
            self.vie.FeatureExtract.attachFeature(mav)

        if uc.get_user_config_var("curve_len", "False") == "True":
            curve_len = pr.features.Curve_len(fs=uc.get_user_config_var('FeatureExtract.sample_rate', 200))
            self.vie.FeatureExtract.attachFeature(curve_len)

        if uc.get_user_config_var("zc", "False") == "True":
            zc = pr.features.Zc(fs=uc.get_user_config_var('FeatureExtract.sample_rate', 200), zc_thresh=uc.get_user_config_var('FeatureExtract.zcThreshold', 0.05))
            self.vie.FeatureExtract.attachFeature(zc)

        if uc.get_user_config_var("ssc", "False") == "True":
            ssc = pr.features.Ssc(fs=uc.get_user_config_var('FeatureExtract.sample_rate', 200), ssc_thresh=uc.get_user_config_var('FeatureExtract.zcThreshold', 0.05))
            self.vie.FeatureExtract.attachFeature(ssc)

        if uc.get_user_config_var("wamp", "False") == "True":
            wamp = pr.features.Wamp(fs=uc.get_user_config_var('FeatureExtract.sample_rate', 200), wamp_thresh=uc.get_user_config_var('FeatureExtract.wampThreshold', 0.05))
            self.vie.FeatureExtract.attachFeature(wamp)

        if uc.get_user_config_var("var", "False") == "True":
            var = pr.features.Var()
            self.vie.FeatureExtract.attachFeature(var)

        if uc.get_user_config_var("vorder", "False") == "True":
            vorder = pr.features.Vorder()
            self.vie.FeatureExtract.attachFeature(vorder)

        if uc.get_user_config_var("logdetect", "False") == "True":
            logdetect = pr.features.Logdetect()
            self.vie.FeatureExtract.attachFeature(logdetect)

        if uc.get_user_config_var("emghist", "False") == "True":
            emghist = pr.features.EMGhist()
            self.vie.FeatureExtract.attachFeature(emghist)

        if uc.get_user_config_var("ar", "False") == "True":
            ar = pr.features.AR()
            self.vie.FeatureExtract.attachFeature(ar)

        if uc.get_user_config_var("ceps", "False") == "True":
            ceps = pr.features.Ceps()
            self.vie.FeatureExtract.attachFeature(ceps)



