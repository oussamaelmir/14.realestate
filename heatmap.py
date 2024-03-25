import time  # Add at the top of your script
from math import sqrt
import pandas as pd
import matplotlib
import geopandas as gpd
import ast
from shapely.geometry import box  # Importing the box function

matplotlib.use('Agg')  # Use the non-interactive 'Agg' backend


def generate_heatmap_data(csv_file, minRooms=1, maxRooms=8, minSize=20, maxSize=500):
    start_time = time.time()  # Start timing

    # Define the percentile for filtering
    pcntl = 0.99

    # Load CSV data
    file_paths = [csv_file]

    dfs = [pd.read_csv(file_path) for file_path in file_paths]
    df = pd.concat(dfs, ignore_index=True)

    # Clean the 'Price' column (remove 'DH' and spaces, and remove EUR/USD)
    df = df[~df['Price'].str.contains('EUR', case=False)]
    df = df[~df['Price'].str.contains('USD', case=False)]
    df['Price'] = df['Price'].str.replace(' DH', '').str.replace(' ', '').str.replace(',', '.').astype(float)

    # Extract numeric values and convert columns to numeric types
    df['Size'] = pd.to_numeric(df['Size'].str.extract('(\d+)')[0], errors='coerce')
    df['Rooms'] = pd.to_numeric(df['Rooms'].str.extract('(\d+)')[0], errors='coerce')
    df['Bedrooms'] = pd.to_numeric(df['Bedrooms'].str.extract('(\d+)')[0], errors='coerce')
    df['Bathrooms'] = pd.to_numeric(df['Bathrooms'].str.extract('(\d+)')[0], errors='coerce')

    # Calculate Price per Square Meter
    df['Price per Square Meter'] = df['Price'] / df['Size']

    # Parse 'Location' column to separate 'lat' and 'lon' columns
    df['Location'] = df['Location'].apply(ast.literal_eval)
    df['lat'] = df['Location'].apply(lambda x: float(x[0]) if x else None)
    df['lon'] = df['Location'].apply(lambda x: float(x[1]) if x else None)

    # Filter out coordinates not in Morocco
    df = df[df['lat'].between(21, 36) & df['lon'].between(-17, -1)]

    # Apply filters
    df_filtered = df[
        (df['Rooms'] >= minRooms) & (df['Rooms'] <= maxRooms) &
        (df['Size'] >= minSize) & (df['Size'] <= maxSize) &
        (df['Price per Square Meter'] <= df['Price per Square Meter'].quantile(pcntl)) &
        (df['Price per Square Meter'] >= df['Price per Square Meter'].quantile(1 - pcntl)) &
        (df['lat'] <= df['lat'].quantile(pcntl)) &
        (df['lat'] >= df['lat'].quantile(1 - pcntl)) &
        (df['lon'] <= df['lon'].quantile(pcntl)) &
        (df['lon'] >= df['lon'].quantile(1 - pcntl))

        ]

    df = df_filtered

    print(f"{len(df)} datapoints generated")

    # Convert to GeoDataFrame and project to Web Mercator
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['lon'], df['lat']), crs='EPSG:4326')
    gdf = gdf.to_crs(epsg=3857)

    print(int(sqrt(len(df))))

    # Define the grid size
    x_min, x_max = gdf.geometry.x.min(), gdf.geometry.x.max()
    y_min, y_max = gdf.geometry.y.min(), gdf.geometry.y.max()
    grid_x_size = int(sqrt(len(df))) * 2  # Number of divisions along x
    grid_y_size = int(sqrt(len(df))) * 2  # Number of divisions along y
    x_step = (x_max - x_min) / grid_x_size
    y_step = (y_max - y_min) / grid_y_size

    # Initialize an empty list to hold the grid cell geometries and their mean values
    cell_data = []

    # Generate grid cells and calculate mean price per square meter in each
    for i in range(grid_x_size):
        for j in range(grid_y_size):
            x_left = x_min + i * x_step
            x_right = x_left + x_step
            y_bottom = y_min + j * y_step
            y_top = y_bottom + y_step

            # Find points within the current cell using spatial indexing
            cell_points = gdf.cx[x_left:x_right, y_bottom:y_top]

            if not cell_points.empty:
                mean_price = cell_points['Price per Square Meter'].mean()
                cell_polygon = box(x_left, y_bottom, x_right, y_top)
                cell_data.append({'geometry': cell_polygon, 'Price per Square Meter': mean_price})

    # Create a GeoDataFrame from the collected cell data
    grid_cells_gdf = gpd.GeoDataFrame(cell_data, crs='EPSG:3857')

    grid_cells_gdf = grid_cells_gdf.to_crs(epsg=4326)

    # Convert grid cells GeoDataFrame to GeoJSON dictionary
    grid_cells_geojson = grid_cells_gdf.to_crs(epsg=4326).__geo_interface__

    # Calculate centroids and construct GeoJSON features
    centroid_features = []
    for index, row in grid_cells_gdf.iterrows():
        centroid = row['geometry'].centroid
        feature = {
            "type": "Feature",
            "properties": {
                "Price per Square Meter": row['Price per Square Meter']
            },
            "geometry": {
                "type": "Point",
                "coordinates": [centroid.x, centroid.y]
            }
        }
        centroid_features.append(feature)

    # Construct centroids GeoJSON dictionary
    centroids_geojson = {
        "type": "FeatureCollection",
        "features": centroid_features
    }

    overall_average_price = df_filtered['Price per Square Meter'].mean()

    end_time = time.time()  # End timing
    print(f"Execution time: {int(end_time - start_time)} seconds")

    # Return grid cells and centroids as GeoJSON dictionaries
    return grid_cells_geojson, centroids_geojson, overall_average_price
