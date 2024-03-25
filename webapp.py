from flask import Flask, request, jsonify, render_template
# Ensure you have the modified generate_heatmap_data function that can accept room filters
from heatmap import generate_heatmap_data

app = Flask(__name__)

# Map cities to their respective CSV files
city_files = {
    'Casablanca': '2024.03.06_13.18_extract_mubawab_vente_casablanca.csv',
    'Rabat': '2024.03.07_02.15_extract_mubawab_vente_rabat.csv',
    'Bouskoura': '2024.03.07_09.06_extract_mubawab_vente_bouskoura.csv',
    'Marrakech': '2024.03.23_21.40_extract_mubawab_vente_marrakech.csv',
    'Tanger': '2024.03.25_03.18_extract_mubawab_vente_tanger.csv',
}

@app.route('/')
def index():
    city = request.args.get('city', 'Casablanca')

    cityCenter = {
        'Casablanca': [33.5731, -7.5898],
        'Rabat': [33.9716, -6.8498],
        'Bouskoura': [33.4551, -7.6616],
        'Marrakech': [31.6295, -7.9811],
        'Tanger': [35.7595, -5.8331]
    }.get(city, [33.5731, -7.5898])

    # Select the CSV file based on the city
    csv_file = city_files.get(city, city_files['Casablanca'])  # Default to Casablanca's file if city is not found

    # Generate the heatmap data based on the selected city's CSV file
    grid_geojson, centroids_geojson, overall_average_price = generate_heatmap_data(csv_file=csv_file)

    # Render the template, passing the city and data to the frontend
    return render_template('index.html', city=city, cityCenter=cityCenter, grid_geojson=grid_geojson,
                           centroids_geojson=centroids_geojson, overall_average_price=overall_average_price)



@app.route('/apply-filter', methods=['POST'])
def apply_filter():
    data = request.get_json()
    city = data['city']

    # Extract the rooms filter. Note: You'll need to adjust the logic to handle the 'all' case and convert '5+' accordingly.
    minRooms = data.get('minRooms')
    maxRooms = data.get('maxRooms')
    minSize = data.get('minSize')
    maxSize = data.get('maxSize')

    csv_file = city_files.get(city, city_files['Casablanca'])
    print(city)

    # Call your modified generate_heatmap_data function with the rooms filter
    # Assuming generate_heatmap_data has been updated to accept a rooms parameter and filter the data accordingly
    grid_geojson, centroids_geojson, overall_average_price = generate_heatmap_data(csv_file=csv_file,
                                                                                   minRooms=minRooms,
                                                                                   maxRooms=maxRooms,
                                                                                   minSize=minSize,
                                                                                   maxSize=maxSize)

    # Return the filtered GeoJSON data
    return jsonify({
        'overallAveragePrice': overall_average_price,
        'grid_geojson': grid_geojson,
        'centroids_geojson': centroids_geojson
    })

if __name__ == '__main__':
    app.run(debug=True)
