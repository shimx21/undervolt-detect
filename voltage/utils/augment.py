import numpy as np
from numpy.lib.stride_tricks import as_strided
from collections import OrderedDict


def register(name):
    def wrapper(cls):
        cls.registered[name] = cls
        return cls
    return wrapper

@register("base")
class AugmentBase:
    registered = {}
    def __init__(self, keepsrc: bool = False, name: str = "base"):
        self.name_ = name
        self.keepsrc_ = keepsrc
    def apply(self, X, y):
        assert NotImplementedError("Base class not implemented")
        
    @staticmethod
    def custom_roll(arr: np.ndarray, roll):
        m = np.asarray(roll)
        arr_roll = arr[:, [*range(arr.shape[1]),*range(arr.shape[1]-1)]].copy()
        strd_0, strd_1 = arr_roll.strides
        n = arr.shape[1]
        result = as_strided(arr_roll, (*arr.shape, n), (strd_0 ,strd_1, strd_1))
        
        return result[np.arange(arr.shape[0]), (n-m)%n]
    
    @classmethod
    def _parse_config(cls, config):
        return cls(**config)
    
    @classmethod
    def from_config(cls, config):
        aug_type = cls.registered[config.pop("type")]
        return aug_type._parse_config(config)
    

@register("roll")
class RollAugment(AugmentBase):
    """Row sequence data"""
    def __init__(self, shift: int = 1000, keepsrc: bool = False, name: str = "roll"):
        super().__init__(keepsrc, name)
        self.shift_ = shift
    def apply(self, X: np.ndarray, y: np.ndarray):
        newdata = np.roll(X, self.shift_, axis=1)
        newlabels = y.copy()
    
        if self.keepsrc_:
            return np.concatenate(X, newdata), np.concatenate(y, newlabels)
        else:
            return newdata, newlabels

@register("rroll")
class RandomRollAugment(AugmentBase):
    """Row sequence data"""
    def __init__(self, n_repeat: int = 1, random_state = None, keepsrc: bool = False, name: str = "rroll"):
        super().__init__(keepsrc, name)
        self.random_state_ = random_state or np.random
        self.n_repeat_ = n_repeat
    def apply(self, X: np.ndarray, y: np.ndarray):
        if self.keepsrc_:
            X_new, y_new = [X], [y]
        else:
            X_new, y_new = [], []
        for i in range(self.n_repeat_):
            n_features = X.shape[1]
            shift = self.random_state_.random_integers(n_features, size=(X.shape[0],))
            X_new.append(self.custom_roll(X, shift))
            y_new.append(y)
    
        return np.concatenate(X_new), np.concatenate(y_new)

# class RandomConcatAugment(AugmentBase):
#     """Randomly concatenate some data"""
#     def __init__(self, name, method, n_sample, ratio, shift):
#         super().__init__(name, method)
#         self.n_sample_ = n_sample
    
#     def apply(self, data):
#         ...

@register("seq")
class SequantialAugment(AugmentBase):
    def __init__(self, *augments: AugmentBase, keepsrc: bool = False, name: str = "seq"):
        super().__init__(keepsrc, name)
        self.augments_ = augments
    
    def apply(self, X, y):
        X_new, y_new = X, y
        for augment in self.augments_:
            X_new, y_new = augment.apply(X_new, y_new)
        
        if self.keepsrc_:
            return np.concatenate(X, X_new), np.concatenate(y, y_new)
        else:
            return X_new, y_new
    
    @classmethod
    def _parse_config(cls, config: OrderedDict):
        """
        {
            "type": "seq",
            "augments": [
                {
                    "type": "aug_type1",
                    "name": "aug1",
                    ...
                },
                {
                    "type": "aug_type2",
                    "name": "aug1",
                    ...
                },
                ...
            ],
            "keepsrc": ...
            "name": ...
        }
        """
        seq = []
        augments = config.pop("augments")
        for aug_config in augments:
            aug_type = cls.registered[aug_config.pop("type")]
            seq.append(aug_type._parse_config(aug_config))
        return cls(*seq, **config)
