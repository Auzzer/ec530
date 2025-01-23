Calculate Distances Between Points: Use the Haversine formula to compute the great-circle distance between each pair of points from the two arrays. The Haversine formula accounts for the Earth's curvature and is defined as:

$$
d=2r \cdot \arcsin \left(\sqrt{\sin ^2\left(\frac{\Delta \varphi}{2}\right)+\cos \left(\varphi_1\right) \cos \left(\varphi_2\right) \sin ^2\left(\frac{\Delta \lambda}{2}\right)}\right)
$$


Where:
- $d$ is the distance between the two points.
- $r$ is the Earth's radius (here I take radius $=6,371 \mathrm{~km}$ for average).
- $\varphi_1$ and $\varphi_2$ are the latitudes of the two points in radians.
- $\Delta \varphi$ is the difference between the latitudes.
- $\Delta \lambda$ is the difference between the longitudes in radians.
  
For simplicity, denote $a=sin^2(\frac{\Delta \varphi}{2})+ cos(\varphi_1)cos(\varphi_2)sin^2(\frac{\Delta \lambda}{2})$.\
This formula calculates the shortest distance over the Earth's surface, giving an "as-the-crow-flies" distance between the points.

Then searching in the large database, we will need some tools to accelerate the indexing speed. Here I utilize the BallTree data structure from the scikit-learn library. This approach significantly optimizes the search for nearest neighbors in large datasets.

# source
[Find nearest neighbors by lat/long using Haversine distance with a BallTree](https://ogrisel.github.io/scikit-learn.org/sklearn-tutorial/modules/generated/sklearn.neighbors.BallTree.html)

[Haversine Formula in Python (Bearing and Distance between two GPS points)](https://gist.github.com/DeanThompson/d5d745eca4e9023c6501)