import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import logging

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ClusteringModel:
    """
    Implementation of clustering algorithms for financial data.
    """

    def __init__(self, n_clusters=3, random_state=42):
        """
        Initializes the clustering model.

        Args:
            n_clusters (int): Number of clusters.
            random_state (int): Seed for reproducibility.
        """
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.model = KMeans(n_clusters=self.n_clusters, random_state=self.random_state)
        self.scaler = StandardScaler()

    def fit(self, data):
        """
        Fits the clustering model to the data.

        Args:
            data (np.array): Input data for clustering.

        Returns:
            np.array: Cluster labels for each data point.
        """
        logging.info("Scaling data for clustering...")
        scaled_data = self.scaler.fit_transform(data)
        logging.info("Fitting KMeans clustering model...")
        cluster_labels = self.model.fit_predict(scaled_data)
        logging.info(f"Clustering completed. Labels: {np.unique(cluster_labels)}")
        return cluster_labels

    def predict(self, new_data):
        """
        Predicts clusters for new data.

        Args:
            new_data (np.array): New input data.

        Returns:
            np.array: Predicted cluster labels.
        """
        scaled_data = self.scaler.transform(new_data)
        logging.info("Predicting clusters for new data...")
        return self.model.predict(scaled_data)

    def cluster_centers(self):
        """
        Returns the cluster centers.

        Returns:
            np.array: Scaled coordinates of cluster centers.
        """
        return self.model.cluster_centers_

    def inertia(self):
        """
        Returns the inertia of the current clustering.

        Returns:
            float: Inertia value.
        """
        return self.model.inertia_
