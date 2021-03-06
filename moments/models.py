import ROOT
import numpy as np
from scipy import stats
from moments.utils import TH1R


class DataRetreiver(object):
    def __init__(self, name, title):
        super(DataRetreiver, self).__init__()
        self.name = name
        self.title = title

    def data(self, *args, **kwargs):
        pass

    def eval(self, *args, **kwargs):
        data = self.data(*args, **kwargs)
        data, edges = np.histogram(data, *args)
        hist = TH1R.form(data, edges, self.name, self.title)
        return hist


class GaussLikeRetreiver(DataRetreiver):
    _formula = 'TMath::Power(x,[0]) * TMath::Exp(- x * x / ([1] * [1]))'

    def __init__(self, name, title, mrange):
        super(GaussLikeRetreiver, self).__init__(name, title)
        self.mrange = mrange

    def func(self, *args, **kwargs):
        a, b = self.mrange
        func = ROOT.TF1('f1', self._formula, a, b)
        func.SetParameter(0, kwargs['gamma'])
        func.SetParameter(1, kwargs['sigma'])
        return func

    def data(self, *args, **kwargs):
        func = self.func(*args, **kwargs)
        data = [func.GetRandom() for i in range(kwargs['ssize'])]
        return data


class GaussLikeAnalyticRetreiver(GaussLikeRetreiver):
    def __init__(self, name, title, mrange):
        super(GaussLikeAnalyticRetreiver, self).__init__(name, title, mrange)

    def eval(self, *args, **kwargs):
        func = self.func(*args, **kwargs)
        data = np.array([func.Eval(i) for i in range(*self.mrange)])
        x, edges = np.histogram(data, *args)
        hist = TH1R.form(data, edges, self.name, self.title)
        if any(np.isnan(data)):
            print data
        return hist


class NBDRetreiver(DataRetreiver):
    def __init__(self, name, title):
        super(NBDRetreiver, self).__init__(name, title)

    def data(self, *args, **kwargs):
        # data = np.random.negative_binomial(29000, 0.9, lamda)
        data = np.random.negative_binomial(**kwargs)
        # print '>>>>>> ', min(data), max(data)
        return data
        # possibly one needs to overload eval
        # data, edges = np.histogram(data, -2971 + 3452, (2971, 3452))


class NBDAnalyticRetreiver(DataRetreiver):
    def __init__(self, name, title):
        super(NBDAnalyticRetreiver, self).__init__(name, title)

    def eval(self, *args, **kwargs):
        x = np.arange(kwargs['start'], kwargs['stop'], 1)
        data = stats.nbinom.pmf(x, kwargs['n'], kwargs['p'])
        x, edges = np.histogram(data, *args)
        hist = TH1R.form(data, edges, self.name, self.title)
        # print '>>>>>>>>', len(data), len(edges)
        if any(np.isnan(data)):
            print 'generated data:', data
        return hist


class RWalkRetreiver(DataRetreiver):
    def __init__(self, name, title):
        super(RWalkRetreiver, self).__init__(name, title)

    def eval(self, *args, **kwargs):
        data, nbins = ROOT.TFile.Open(self.name + '.root'), args[0]
        self.name = self.name + '_' + str(nbins)
        a, b = data.random_walks.GetMinimum(
            'gratio'), data.random_walks.GetMaximum('gratio')
        hist = TH1R(self.name, 'nbins = %d, ' %
                    nbins + self.title, nbins, a, b)
        data.random_walks.Draw('gratio >> ' + self.name)
        return hist


class BinMoment(object):
    def __init__(self, histogram):
        super(BinMoment, self).__init__()
        self.histogram = histogram

    def bins(self):
        N = self.histogram.GetNbinsX()
        # print 'Warning manually deleting zero bins'
        bins = np.array([self.histogram.GetBinContent(i)
                         for i in range(1, N + 1)])
        return bins, N

    def moments(self):
        bins, N = self.bins()
        # Duplicate N times original array
        A = np.repeat(bins[::-1], N, axis=0)
        A = np.array([np.append(bins[::-1][i:], np.zeros(i))
                      for i in range(len(bins))])[::-1]
        b = bins * np.array([i for i in range(1, N + 1)])

        # print 'bins', bins
        # print 'args', b
        # print 'matrix:\n', A

        return np.linalg.solve(A, b)
