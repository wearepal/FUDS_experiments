# The evaluation of the performance of the LFR algorithm for different states:

# TIME SHIFT


# The packages to download:


from aif360.algorithms.preprocessing import LFR
from aif360.datasets import StandardDataset
from aif360.metrics import ClassificationMetric
from folktables import ACSDataSource, ACSEmployment
import numpy as np
from sklearn.preprocessing import StandardScaler


def main():
    # Load the data:
    state_list_short = [
        "CA",
        "AK",
        "HI",
        "KS",
        "NE",
        "ND",
        "NY",
        "OR",
        "PR",
        "TX",
        "VT",
        "WY",
    ]
    data_source = ACSDataSource(survey_year="2014", horizon="1-Year", survey="person")

    # We perform the evaluation for each state:

    for state in state_list_short:

        FPR_LFR = np.array([])
        FNR_LFR = np.array([])
        TPR_LFR = np.array([])
        PPV_LFR = np.array([])
        FOR_LFR = np.array([])
        ACC_LFR = np.array([])

        acs_data = data_source.get_data(states=[state], download=True)
        data = acs_data[feat]
        features, label, group = ACSEmployment.df_to_numpy(acs_data)
        # stick to instances with no NAN values
        data = data.dropna()
        index = data.index
        a_list = list(index)
        new_label = label[a_list]
        data["label"] = new_label
        favorable_classes = [True]
        protected_attribute_names = ["SEX"]
        privileged_classes = np.array([[1]])
        data_all = StandardDataset(
            data,
            "label",
            favorable_classes=favorable_classes,
            protected_attribute_names=protected_attribute_names,
            privileged_classes=privileged_classes,
        )
        privileged_groups = [{"SEX": 1}]
        unprivileged_groups = [{"SEX": 2}]
        dataset_orig = data_all

        for _ in range(10):  # 10-fold cross validation, save values for each fold.
            dataset_orig_train, dataset_orig_test = dataset_orig.split([0.7], shuffle=True)

            scale_orig = StandardScaler()
            dataset_orig_train.features = scale_orig.fit_transform(dataset_orig_train.features)

            TR = LFR(
                unprivileged_groups=unprivileged_groups,
                privileged_groups=privileged_groups,
                k=10,
                Ax=0.1,
                Ay=1.0,
                Az=2.0,
                verbose=1,
            )
            TR = TR.fit(dataset_orig_train, maxiter=5000, maxfun=5000)

            TR.transform(dataset_orig_train)

            # test the classifier:

            dataset_orig_test.features = scale_orig.transform(dataset_orig_test.features)
            dataset_transf_test = TR.transform(dataset_orig_test)

            dataset_transf_test_new = dataset_orig_test.copy(deepcopy=True)
            dataset_transf_test_new.scores = dataset_transf_test.scores

            fav_inds = dataset_transf_test_new.scores > 0.5
            dataset_transf_test_new.labels[fav_inds] = 1.0
            dataset_transf_test_new.labels[~fav_inds] = 0.0

            cm_transf_test = ClassificationMetric(
                dataset_orig_test,
                dataset_transf_test_new,
                unprivileged_groups=unprivileged_groups,
                privileged_groups=privileged_groups,
            )
            fpr = cm_transf_test.difference(cm_transf_test.false_positive_rate)
            fnr = cm_transf_test.difference(cm_transf_test.false_negative_rate)
            tpr = cm_transf_test.difference(cm_transf_test.true_positive_rate)
            ppv = cm_transf_test.difference(cm_transf_test.positive_predictive_value)
            fom = cm_transf_test.difference(cm_transf_test.false_omission_rate)
            acc = cm_transf_test.accuracy()

            FPR_LFR = np.append(FPR_LFR, fpr)
            FNR_LFR = np.append(FNR_LFR, fnr)
            TPR_LFR = np.append(TPR_LFR, tpr)
            PPV_LFR = np.append(PPV_LFR, ppv)
            FOR_LFR = np.append(FOR_LFR, fom)
            ACC_LFR = np.append(ACC_LFR, acc)

        filename = "Adult_time_gender_LFR_eval_" + state + ".txt"

        with open(filename, "w") as a_file:
            res = [FPR_LFR, FNR_LFR, TPR_LFR, PPV_LFR, FOR_LFR, ACC_LFR]

            for metric in res:
                np.savetxt(a_file, metric)


if __name__ == "__main__":
    main()