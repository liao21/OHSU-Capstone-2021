# receives commands from web interface and creates a list of class instances with each selected feature

from pattern_rec import features
from utilities.user_config import get_user_config_var


class FeaturesSelected(object):

    def __init__(self, vie):

        self.vie = vie

    def create_instance_list(self):

        sample_rate = get_user_config_var('FeatureExtract.sample_rate', 200)

        if get_user_config_var("mav", True):
            mav = features.Mav()
            self.vie.attach_feature(mav)

        if get_user_config_var("curve_len", True):
            curve_len = features.CurveLen()
            self.vie.attach_feature(curve_len)

        if get_user_config_var("zc", True):
            zc = features.Zc(fs=sample_rate, zc_thresh=get_user_config_var('FeatureExtract.zc_threshold', 0.05))
            self.vie.attach_feature(zc)

        if get_user_config_var("ssc", True):
            ssc = features.Ssc(fs=sample_rate, ssc_thresh=get_user_config_var('FeatureExtract.ssc_threshold', 0.05))
            self.vie.attach_feature(ssc)

        if get_user_config_var("wamp", False):
            wamp = features.Wamp(fs=sample_rate, wamp_thresh=get_user_config_var('FeatureExtract.wamp_threshold', 0.05))
            self.vie.attach_feature(wamp)

        if get_user_config_var("var", False):
            var = features.Var()
            self.vie.attach_feature(var)

        if get_user_config_var("vorder", False):
            vorder = features.Vorder()
            self.vie.attach_feature(vorder)

        if get_user_config_var("logdetect", False):
            logdetect = features.LogDetect()
            self.vie.attach_feature(logdetect)

        if get_user_config_var("emghist", False):
            emghist = features.EmgHist()
            self.vie.attach_feature(emghist)

        if get_user_config_var("ar", False):
            ar = features.AR()
            self.vie.attach_feature(ar)

        if get_user_config_var("ceps", False):
            ceps = features.Ceps()
            self.vie.attach_feature(ceps)
