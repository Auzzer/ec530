import numpy as np
from sklearn.neighbors import BallTree

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Using haversine metric to calculate the distance between two points 
    on the Earth's surface.
    
    Parameters:
        lat1, lon1: Latitude and longitude of point 1 in degrees.
        lat2, lon2: Latitude and longitude of point 2 in degrees.
        
    Returns:
        Distance in kilometers between the two points.
    """
    # Earth's radius in kilometers
    r= 6371.0
    
    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    Delta_phi = lat2 - lat1
    Detla_lambda = lon2 - lon1
    
    a = np.sin(Delta_phi / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(Detla_lambda / 2)**2
    d = 2 * r*np.arcsin(np.sqrt(a))
    return d

def find_closest_points(array1, array2):
    """
    Match each point in array1 to the closest point in array2.
    Find the nearest neighbors using sklearn's BallTree algorithm:
    https://ogrisel.github.io/scikit-learn.org/sklearn-tutorial/modules/generated/sklearn.neighbors.BallTree.html
    Parameters:
        array1: Array of points (latitude, longitude) - shape (N, 2)
        array2: Array of points (latitude, longitude) - shape (M, 2)
        
    Returns:
        A list of indices from array2 that are the closest points to each point in array1.
    """
    
    # Convert degrees to radians for BallTree
    array2_radians = np.radians(array2)
    
    # Create a BallTree for efficient nearest neighbor search
    tree = BallTree(array2_radians, metric='haversine')
    
    # Convert array1 to radians
    array1_radians = np.radians(array1)
    
    # Query the nearest neighbors
    distances, indices = tree.query(array1_radians, k=1)
    
    # Convert distances from radians to kilometers
    distances_km = distances.flatten() * 6371.0
    
    return indices.flatten(), distances_km

# Example usage
array1 = np.array([[37.7749, -122.4194], [34.0522, -118.2437]])  # San Francisco and Los Angeles
array2 = np.array([[40.7128, -74.0060], [36.1699, -115.1398], [25.7617, -80.1918]])  # NYC, Las Vegas, Miami

closest_indices, closest_distances = find_closest_points(array1, array2)

# Output the closest point indices, distances and points
print("Closest points indices:", closest_indices)
print("Closest distances (km):", closest_distances)
print("Closest points:", array2[closest_indices])
