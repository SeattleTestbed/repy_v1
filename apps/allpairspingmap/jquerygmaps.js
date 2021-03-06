// Function to run at page load
$(document).ready(function() {
  function initialize_map() {
    // Initialize map inside #map div element
    var map = new GMap2(document.getElementById('map'));
    map.setUIToDefault();

    // Set up points for Seattle nodes
    var markers = [];
    $("ul#coords li").each(function(i) {
      // Do we have this node's location data?
      if ($(this).children(".latitude").length) {
        var latitude = $(this).children(".latitude").text();
        var longitude = $(this).children(".longitude").text();
        var point = new GLatLng(latitude, longitude);
        marker = new GMarker(point);
        map.addOverlay(marker);
        marker.setImage("map_marker_icon.png");
        map.setCenter(point, 2);
        markers[i] = marker;
      }
    });

    // Pan to point when clicked
    $(markers).each(function(i, marker) {
      GEvent.addListener(marker, "click", function(){
        displayPoint(marker, i);
      });
    });
    return map;
  }

  // Whenever a marker is clicked, pan to it and move/populate the tooltip div
  function displayPoint(marker, i) {
    map.panTo(marker.getPoint());
    var markerOffset = map.fromLatLngToDivPixel(marker.getPoint());

    // Get node information from adjacency table
    var nodeip = $("#node" + i).children(".nodeip").text();
    var nodelocation = $("#node" + i).children(".locationname").text();
    var nodelat = $("#node" + i).children(".latitude").text();
    var nodelong = $("#node" + i).children(".longitude").text();

    // Populate #message div with node information
    $("#message").empty().append("<strong>Node IP:</strong> " + nodeip + "<br /><strong>Location:</strong> " + nodelocation + "<br /><strong>Lat/Long:</strong> " + nodelat + "/" + nodelong);

    // Finally, display the #message div tooltip
    $("#message").show().css({ top:markerOffset.y, left:markerOffset.x });
  }
  
  
  // Only initialize the map if we have some geoip data to display
  if ($(".latitude").length) {
    var map = initialize_map();
    $("#message").appendTo(map.getPane(G_MAP_FLOAT_SHADOW_PANE));
    var selected_node;
    var selected_marker;
    var selected_location;
    var line;
  } else {
    // Remove the map constraints if we can't display the map
    $('#map').css('width', 'auto').css('height', 'auto').text('No location data loaded!')
  }
  
  if ($('.lookingup').length)
    // Reload after 5 seconds
    setTimeout(function() {location.reload()}, 5000)

});
