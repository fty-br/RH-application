<?php
// URL pour récupérer les résultats de matching depuis Flask
$url = 'http://localhost:5000/match';

// Effectuer une requête GET pour récupérer les résultats de matching
$response = file_get_contents($url);

// Décoder les données JSON
$matching_results = json_decode($response, true);

// Initialiser les tableaux pour les données du graphique
$cv_job_ids = [];
$similarities = [];

// Vérifier si des résultats sont disponibles
if ($matching_results) {
    // Parcourir les résultats de matching pour récupérer les données nécessaires pour le graphique
    foreach ($matching_results as $result) {
        $cv_job_ids[] = $result['cv_job_id'];
        $similarities[] = $result['similarity'];
    }
}

// Convertir les données du graphique en format JSON
$graph_data_json = json_encode(['cv_job_ids' => $cv_job_ids, 'similarities' => $similarities]);
?>



<!doctype html>
<html>
    <head>
        <title> Micro credentials app using Php and python flask </title>
        <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Graphique interactif de similarité entre CV et Offres d'emploi</title>
    <!-- Inclure la bibliothèque Plotly.js -->
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>

    <body>
        <form method="POST" action="">
            <label for="username">Username </label>
            <input type="text" id="username" name="username"><label></label>
<br>
            <label for="password">Password </label>
            <input type="password" id="password" name="password"><label></label>
<br>
            <button type="submit"> submit </button>
        </form>

        <?php

        if($_SERVER['REQUEST_METHOD'] === 'POST'){
            $username = $_POST['username'];
            $password = $_POST['password'];

            $response = file_get_contents('http://localhost:5000/validate?username='.urldecode($username). '&password=' .urlencode ($password));
            
            echo $response;


        }
        ?>
        
        <div id="graph"></div>
    
        <script>
            // Récupérer les données JSON générées par PHP
            var graphData = <?php echo $graph_data_json; ?>;
    
            // Créer le graphique interactif avec Plotly.js
            var trace = {
                x: graphData.cv_job_ids,
                y: graphData.similarities,
                type: 'bar',
                marker: {
                    color: 'rgb(51, 122, 183)' // Couleur des barres
                }
            };
            var layout = {
                title: 'Similarité entre CV et Offres d\'emploi',
                xaxis: { title: 'CV - Offre d\'emploi' },
                yaxis: { title: 'Similarité' },
                margin: { t: 50 }
            };
            var data = [trace];
            Plotly.newPlot('graph', data, layout);
        </script>
    </body>
</html>