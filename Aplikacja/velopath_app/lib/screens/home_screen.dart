import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class HomeScreen extends StatefulWidget{
    const HomeScreen({super.key});

    @override
    State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final MapController _mapController = MapController();

  static const LatLng _initialCenter = LatLng(50.3497, 18.2261);
  static const String _mapTilerApiKey = String.fromEnvironment('MAPTILER_API_KEY');

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Home Screen'),
      ),
      body: FlutterMap(
        options: MapOptions(
          initialCenter: _initialCenter,
          initialZoom: 13.0,
        ),
        children: [
            TileLayer(
                urlTemplate: 'https://api.maptiler.com/maps/basic-v2/256/{z}/{x}/{y}.png?key=$_mapTilerApiKey',
                userAgentPackageName: 'com.velopath.app',
            ),
            RichAttributionWidget(
                alignment: AttributionAlignment.bottomRight,
                attributions:[
                    TextSourceAttribution('OpenStreetMap contributors', onTap: () {}),
                     TextSourceAttribution('Maptiler', onTap: () {}),
                ]
            )
        ],
      ),
    );
  }
}