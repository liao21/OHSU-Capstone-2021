from abc import ABCMeta, abstractmethod
import numpy as np
import math
from spectrum import aryule


# Abstract base class
class EMGFeatures(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def get_name(self):
        pass

    # All methods with this decorator must be overloaded
    @abstractmethod
    def extract_features(self, data_input):
        pass


class Mav(EMGFeatures):
    def __init__(self):
        super(Mav, self).__init__()

        self.name = "Mav"

    def get_name(self):
        return self.name

    def extract_features(self, data_input):
        """ Mean Absolute Value

        Compute mav across all samples (axis=0)

        :param data_input: input samples to compute feature
        :return: scalar feature value
        """

        mav_feature = np.mean(abs(data_input), 0)
        return mav_feature


class CurveLen(EMGFeatures):
    def __init__(self, fs=200):
        super(CurveLen, self).__init__()

        self.fs = fs
        self.name = "Curve_len"

    def get_name(self):
        return self.name

    def extract_features(self, data_input):
        """ Curve Length Feature
        Curve length is the sum of the absolute value of the derivative of the
        signal, normalized by the sample rate

        :param data_input: input samples to compute feature
        :return: scalar feature value
        """

        # Number of Samples
        n = data_input.shape[0]

        curve_len_feature = np.sum(abs(np.diff(data_input, axis=0)), axis=0) * self.fs / n
        return curve_len_feature


class Zc(EMGFeatures):
    def __init__(self, fs=200, zc_thresh=0.05):
        super(Zc, self).__init__()

        self.fs = fs
        self.zc_thresh = zc_thresh
        self.name = "Zc"

    def get_name(self):
        return self.name

    def extract_features(self, data_input):
        """ Zero-crossings
        Criteria for crossing zero
        zeroCross=(y[iSample] - t > 0 and y[iSample + 1] - t < 0) or (y[iSample] - t < 0 and y[iSample + 1] - t > 0)
        overThreshold=abs(y[iSample] - t - y[iSample + 1] - t) > zc_thresh
        if zeroCross and overThreshold:
            # Count a zero cross
            zc[iChannel]=zc[iChannel] + 1

        :param data_input: input samples to compute feature
        :return: scalar feature value
        """
        # Number of Samples
        n = data_input.shape[0]

        # Value to compute 'zero-crossing' around
        t = 0.0

        zc_feature = np.sum(
            ((data_input[0:n - 1, :] - t > 0) & (data_input[1:n, :] - t < 0) |
             (data_input[0:n - 1, :] - t < 0) & (data_input[1:n, :] - t > 0)) &
            (abs(data_input[0:n - 1, :] - t - data_input[1:n, :] - t) > self.zc_thresh),
            axis=0) * self.fs / n
        return zc_feature


class Ssc(EMGFeatures):
    def __init__(self, fs=200, ssc_thresh=0.15):
        super(Ssc, self).__init__()

        self.fs = fs
        self.ssc_thresh = ssc_thresh
        self.name = "Ssc"

    def get_name(self):
        return self.name

    def extract_features(self, data_input):
        """ Slope Sign Changes

        Criteria for counting slope sign changes:

        signChange = (y[iSample] > y[iSample - 1]) and
            (y[iSample] > y[iSample + 1]) or (y[iSample] < y[iSample - 1]) and (y[iSample] < y[iSample + 1])

        overThreshold=abs(y[iSample] - y[iSample + 1]) > ssc_thresh or abs(y[iSample] - y[iSample - 1]) > ssc_thresh

        if signChange and overThreshold:
            # Count a slope change
            ssc[iChannel]=ssc[iChannel] + 1

        :param data_input: input samples to compute feature
        :return: scalar feature value
        """
        # Number of Samples
        n = data_input.shape[0]

        ssc_feature = np.sum(
            ((data_input[1:n - 1, :] > data_input[0:n - 2, :]) & (data_input[1:n - 1, :] > data_input[2:n, :]) |
             (data_input[1:n - 1, :] < data_input[0:n - 2, :]) & (data_input[1:n - 1, :] < data_input[2:n, :])) &
            ((abs(data_input[1:n - 1, :] - data_input[2:n, :]) > self.ssc_thresh) |
             (abs(data_input[1:n - 1, :] - data_input[0:n - 2, :]) > self.ssc_thresh)), axis=0
        ) * self.fs / n
        return ssc_feature


class Wamp(EMGFeatures):
    def __init__(self, fs=200, wamp_thresh=0.05):
        super(Wamp, self).__init__()

        self.fs = fs
        self.wamp_thresh = wamp_thresh
        self.name = "Wamp"

    def get_name(self):
        return self.name

    def extract_features(self, data_input):
        """ Willison Amplitude
        "This feature is defined as the amount of times that the
        change in EMG signal amplitude exceeds a threshold; it is
        an indicator of the firing of motor unit action potentials
        and is thus a surrogate metric for the level of muscle contraction." (Tkach et. al 4)

        wamp = sum of f(abs(data_input[iSample] - data_input[iSample + 1])) in an analysis time window with n samples
        where f(x) = 1 if data_input[iSample] - data_input[iSample + 1]) > wamp_thresh and f(x) = 0 else

        :param data_input: input samples to compute feature
        :return: scalar feature value
        """

        # Number of Samples
        n = data_input.shape[0]

        wamp_feature = np.sum(
            ((abs(data_input[1:n - 1, :] - data_input[0:n - 2, :])) > self.wamp_thresh), axis=0) * self.fs / n
        return wamp_feature


class Var(EMGFeatures):
    def __index__(self):
        super(Var, self).__init__()

        self.name = "Var"

    def get_name(self):
        return self.name

    def extract_features(self, data_input):
        """ Variance
        "This feature is the measure of the EMG signal's power." (Tkach et. al 4)

        var = sum of signal x squared in an analysis time window with n samples all over (n-1)

        :param data_input: input samples to compute feature
        :return: scalar feature value
        """

        # Number of Samples
        n = data_input.shape[0]

        var_feature = np.sum(np.square(data_input), axis=0) / (n-1)
        return var_feature


class Vorder(EMGFeatures):
    def __index__(self):
        super(Vorder, self).__init__()

        self.name = "Vorder"

    def get_name(self):
        return self.name

    def extract_features(self, data_input):
        """ V-Order Feature

        "This metric yields an estimation of the exerted muscle force...
        characterized by the absolute value of EMG signal
        to the vth power. The applied smoothing filter is the moving
        average window. Therefore, this feature is defined as
        , where E is the expectation operator
        applied on the samples in one analysis window. One study
        indicates that the best value for v is 2, which leads to
        the definition of the EMG v-Order feature as the same as
        the square root of the var feature." (Tkach et. al 4)

        vorder = sqrt(sum of signal x squared in an analysis time window with n samples, over (n-1))

        :param data_input: input samples to compute feature
        :return: scalar feature value
        """

        # Number of Samples
        n = data_input.shape[0]

        vorder_feature = np.sqrt(np.sum(np.square(data_input), axis=0) / (n-1))
        return vorder_feature


class LogDetect(EMGFeatures):
    def __index__(self):
        super(LogDetect, self).__init__()

        self.name = "Logdetect"

    def get_name(self):
        return self.name

    def extract_features(self, data_input):
        """ V-Order
        "This metric yields an estimation of the exerted muscle force" (Tkach et. al 4)

        logdetect = e raised to (the mean of the log of the absolute value of the signal input)

        :param data_input: input samples to compute feature
        :return: scalar feature value
        """

        logdetect_feature = math.e**(np.mean(np.log(abs(data_input)), axis=0))
        return logdetect_feature


class EmgHist(EMGFeatures):
    def __index__(self):
        super(EmgHist, self).__init__()

        self.name = "EmgHist"

    def get_name(self):
        return self.name

    def extract_features(self, data_input):
        """ EMG Histogram
        "This feature provides information about the frequency
        with which the EMG signal reaches various amplitudes" (Tkach et. al 5)

        Actual feature finds the frequencies with the max and min amplitude and
        sets the difference of this as the range for a histogram with multiple
        data bins.

        This feature would result in multiple values for each channel, this would cause
        problems since an array with more than 8 values would be returned.  Rather than returning
        the number of frequencies with amplitudes in each equally spaced bin, it returns the range
        in between the max and min amplitude for each channel

        :param data_input: input samples to compute feature
        :return: feature value
        """

        emghist_feature = []
        for channel in range(8):
            emghist_range = (np.amax(np.hstack(data_input[:, channel:channel+1]))) - \
                            (np.amin(np.hstack(data_input[:, channel:channel+1])))
            emghist_feature.append(emghist_range)

        return emghist_feature


class AR(EMGFeatures):
    def __index__(self):
        super(AR, self).__init__()

        self.name = "AR"

    def get_name(self):
        return self.name

    def extract_features(self, data_input):
        """ Autoregressive Coefficient
        "This feature models individual EMG signals as a linear
        autoregressive time series and provides information
        about the muscle's contraction state" (Tkach et. al 5)

        uses time-series analysis library spectrum to compute single
        order autoregressive model coefficients using Yule-Walker equations for each
        channel and contructs an array made up of the autoregressive coeffcients (a sub 1 since only first order)
        for each channel

        :param data_input: input samples to compute feature
        :return: feature value
        """

        ar_feature = []
        for channel in range(8):
            ar_coefficient_array, noise, reflection = aryule(np.hstack(data_input[:, channel:channel+1]), 1)
            ar_coefficient = ar_coefficient_array[0]
            ar_feature.append(ar_coefficient)

        return ar_feature


class Ceps(EMGFeatures):
    def __index__(self):
        super(Ceps, self).__init__()

        self.name = "Ceps"

    def get_name(self):
        return self.name

    def extract_features(self, data_input):
        """ Cepstrum coefficients
        "This measure provides information about the rate of
        change in different frequency spectrum bands of a signal." (Tkach et. al 5)

        since c sub 1 = -a sub 1, this will be the case for all channels since first order
        uses time-series analysis library spectrum to compute single
        order autoregressive model coefficients using Yule-Walker equations for each
        channel and contructs an array made up of the cepstrum coeffcients (-a sub 1 since only first order)
        for each channel

        :param data_input: input samples to compute feature
        :return: scalar feature value

        """

        ceps_feature = []
        for channel in range(8):
            ar_coefficient_array, noise, reflection = aryule(np.hstack(data_input[:, channel:channel+1]), 1)
            ar_coefficient = ar_coefficient_array[0]
            ceps_coefficient = -ar_coefficient
            ceps_feature.append(ceps_coefficient)

        return ceps_feature
