
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'confirmacion_screen.dart';
import '../services/qr_service.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final MobileScannerController _scannerController =
      MobileScannerController();

  final QrService _qrService = QrService();

  bool _qrDetectado = false;
  bool _validando = false;

  String? _error;
  String? _tokenQr;

  Map<String, dynamic>? _datosQr;

  Future<void> _alDetectarQR(BarcodeCapture capture) async {
    if (_qrDetectado) return;

    final codigo = capture.barcodes.firstOrNull?.rawValue;

    if (codigo == null || codigo.isEmpty) return;

    setState(() {
      _qrDetectado = true;
      _validando = true;
      _error = null;
      _datosQr = null;
      _tokenQr = codigo;
    });

    await _scannerController.stop();

    try {
      final respuesta = await _qrService.validarQr(codigo);

      if (!mounted) return;

      setState(() {
        _datosQr = respuesta;
        _validando = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _error = e.toString().replaceFirst('Exception: ', '');
        _validando = false;
      });
    }
  }

  Future<void> _escanearOtro() async {
    setState(() {
      _qrDetectado = false;
      _validando = false;
      _error = null;
      _datosQr = null;
      _tokenQr = null;
    });

    await _scannerController.start();
  }

  @override
  void dispose() {
    _scannerController.dispose();
    super.dispose();
  }

  Widget _mostrarDatos() {
    final vehiculo = _datosQr!['vehiculo'] as Map<String, dynamic>;
    final empresa = _datosQr!['empresa'] as Map<String, dynamic>;
    final cupo = _datosQr!['cupo'] as Map<String, dynamic>;
    final tiquete = _datosQr!['tiquete'] as Map<String, dynamic>;

    return Card(
      margin: const EdgeInsets.all(20),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.check_circle, color: Colors.green, size: 28),
                SizedBox(width: 10),
                Text(
                  'QR válido',
                  style: TextStyle(
                    fontSize: 21,
                    fontWeight: FontWeight.bold,
                    color: Colors.green,
                  ),
                ),
              ],
            ),
            const Divider(height: 30),
            _dato('Placa', vehiculo['placa']),
            _dato('Empresa', empresa['nombre_empresa']),
            _dato('Modelo', vehiculo['modelo'] ?? 'No registrado'),
            _dato('Capacidad del tanque', '${vehiculo['capacidad_tanque']} L'),
            _dato('Litros asignados', '${cupo['litros_asignados']} L'),
            _dato('Litros disponibles', '${cupo['litros_disponibles']} L'),
            _dato('Estado del tiquete', tiquete['estado']),
            const SizedBox(height: 20),

            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ConfirmacionScreen(
                        datosQr: _datosQr!,
                        tokenQr: _tokenQr!,
                      ),
                    ),
                  );
                },
                child: const Text('CONTINUAR CON EL DESPACHO'),
              ),
            ),
            const SizedBox(height: 10),

            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _escanearOtro,
                child: const Text('ESCANEAR OTRO QR'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _dato(String etiqueta, dynamic valor) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Escanear código QR'),
        backgroundColor: const Color(0xFF123B5D),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            onPressed: () => _scannerController.toggleTorch(),
            icon: const Icon(Icons.flash_on),
            tooltip: 'Linterna',
          ),
        ],
      ),
      body: _qrDetectado
          ? Center(
              child: SingleChildScrollView(
                child: _validando
                    ? const Padding(
                        padding: EdgeInsets.all(30),
                        child: Column(
                          children: [
                            CircularProgressIndicator(),
                            SizedBox(height: 20),
                            Text('Validando código QR...'),
                          ],
                        ),
                      )
                    : _error != null
                        ? Padding(
                            padding: const EdgeInsets.all(20),
                            child: Column(
                              children: [
                                const Icon(
                                  Icons.error_outline,
                                  color: Colors.red,
                                  size: 55,
                                ),
                                const SizedBox(height: 15),
                                const Text(
                                  'No se pudo validar el QR',
                                  style: TextStyle(
                                    fontSize: 20,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 10),
                                Text(
                                  _error!,
                                  textAlign: TextAlign.center,
                                ),
                                const SizedBox(height: 20),
                                FilledButton(
                                  onPressed: _escanearOtro,
                                  child: const Text('INTENTAR OTRO QR'),
                                ),
                              ],
                            ),
                          )
                        : _datosQr != null
                            ? _mostrarDatos()
                            : const SizedBox.shrink(),
              ),
            )
          : Column(
              children: [
                const Padding(
                  padding: EdgeInsets.all(20),
                  child: Text(
                    'Ubica el código QR del vehículo dentro del recuadro.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 16),
                  ),
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      child: MobileScanner(
                        controller: _scannerController,
                        onDetect: _alDetectarQR,
                      ),
                    ),
                  ),
                ),
                const Padding(
                  padding: EdgeInsets.all(20),
                  child: Text(
                    'SIGODIESEL B2B · Validación de despachos',
                    style: TextStyle(color: Colors.grey),
                  ),
                ),
              ],
            ),
    );
  }
}
