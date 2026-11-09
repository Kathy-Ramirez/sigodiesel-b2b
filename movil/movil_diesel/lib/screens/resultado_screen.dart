
import 'package:flutter/material.dart';

class ResultadoScreen extends StatelessWidget {
  final Map<String, dynamic> despacho;

  const ResultadoScreen({
    super.key,
    required this.despacho,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Resultado del despacho'),
        backgroundColor: const Color(0xFF123B5D),
        foregroundColor: Colors.white,
        automaticallyImplyLeading: false,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(22),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Icon(
                    Icons.check_circle,
                    color: Colors.green,
                    size: 75,
                  ),
                  const SizedBox(height: 15),
                  const Text(
                    '¡Despacho registrado!',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 23,
                      fontWeight: FontWeight.bold,
                      color: Colors.green,
                    ),
                  ),
                  const Divider(height: 35),
                  _dato('Placa', despacho['placa']),
                  _dato('Empresa', despacho['empresa']),
                  _dato('Estación', despacho['estacion']),
                  _dato('Número de isla', despacho['nro_isla']),
                  _dato(
                    'Litros cargados',
                    '${despacho['litros_cargados']} L',
                  ),
                  _dato(
                    'Litros disponibles',
                    '${despacho['litros_disponibles']} L',
                  ),
                  _dato(
                    'Estado del despacho',
                    despacho['estado_transaccion'],
                  ),
                  _dato(
                    'Estado del tiquete',
                    despacho['estado_tiquete'],
                  ),
                  const SizedBox(height: 25),
                  FilledButton(
                    onPressed: () {
                      Navigator.of(context).popUntil(
                        (route) => route.isFirst,
                      );
                    },
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF123B5D),
                      padding: const EdgeInsets.symmetric(vertical: 15),
                    ),
                    child: const Text('VOLVER AL ESCÁNER'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _dato(String etiqueta, dynamic valor) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Expanded(
            child: Text(
              etiqueta,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
          Expanded(
            child: Text(
              valor?.toString() ?? '-',
              textAlign: TextAlign.end,
            ),
          ),
        ],
      ),
    );
  }
}
