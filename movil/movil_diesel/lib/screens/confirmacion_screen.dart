import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import '../services/despacho_service.dart';
import 'resultado_screen.dart';

class ConfirmacionScreen extends StatefulWidget {
  final Map<String, dynamic> datosQr;
  final String tokenQr;
  

  const ConfirmacionScreen({
    super.key,
    required this.datosQr,
    required this.tokenQr,
  });

  @override
  State<ConfirmacionScreen> createState() =>
      _ConfirmacionScreenState();
}

class _ConfirmacionScreenState extends State<ConfirmacionScreen> {
  final _formKey = GlobalKey<FormState>();
  final _litrosController = TextEditingController();
  final _islaController = TextEditingController();
  final DespachoService _despachoService = DespachoService();
  final Uuid _uuid = Uuid();

  bool _cargando = false;
  String? _idOperacion;

  @override
  void dispose() {
    _litrosController.dispose();
    _islaController.dispose();
    super.dispose();
  }

  
  Future<void> _confirmarDespacho() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _cargando = true;
    });

    // Se genera una sola vez y se conserva para los reintentos.
    _idOperacion ??= _uuid.v4();

    try {
      final litros = double.parse(
        _litrosController.text.trim().replaceAll(',', '.'),
      );

      final respuesta = await _despachoService.registrarDespacho(
        tokenQr: widget.tokenQr,
        litrosCargados: litros,
        nroIsla: _islaController.text.trim(),
        idOperacion: _idOperacion!,
      );

      if (!mounted) return;

      final despacho = Map<String, dynamic>.from(
        respuesta['despacho'] as Map,
      );

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => ResultadoScreen(
            despacho: despacho,
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            e.toString().replaceFirst('Exception: ', ''),
          ),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _cargando = false;
        });
      }
    }
  }


  @override
  Widget build(BuildContext context) {
    final vehiculo = widget.datosQr['vehiculo'];
    final empresa = widget.datosQr['empresa'];
    final cupo = widget.datosQr['cupo'];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Confirmar despacho'),
        backgroundColor: const Color(0xFF123B5D),
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Datos del vehículo',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 15),

              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      _dato('Placa', vehiculo['placa']),
                      _dato(
                        'Empresa',
                        empresa['nombre_empresa'],
                      ),
                      _dato(
                        'Litros disponibles',
                        '${cupo['litros_disponibles']} L',
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 25),

              const Text(
                'Datos del despacho',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 15),

              TextFormField(
                controller: _litrosController,
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                decoration: const InputDecoration(
                  labelText: 'Litros a cargar',
                  suffixText: 'L',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.local_gas_station),
                ),
                validator: (value) {
                  final litros = double.tryParse(
                    (value ?? '').replaceAll(',', '.'),
                  );

                  if (litros == null || litros <= 0) {
                    return 'Ingresa una cantidad válida.';
                  }

                  final disponibles = double.tryParse(
                        cupo['litros_disponibles'].toString(),
                      ) ??
                      0;

                  if (litros > disponibles) {
                    return 'Supera los litros disponibles.';
                  }

                  final capacidad = double.tryParse(
                        vehiculo['capacidad_tanque'].toString(),
                      ) ??
                      0;

                  if (litros > capacidad) {
                    return 'Supera la capacidad del tanque.';
                  }

                  return null;
                },
              ),

              const SizedBox(height: 18),

              TextFormField(
                controller: _islaController,
                decoration: const InputDecoration(
                  labelText: 'Número de isla',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.pin_drop_outlined),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Ingresa el número de isla.';
                  }

                  if (value.trim().length > 20) {
                    return 'El número de isla es demasiado largo.';
                  }

                  return null;
                },
              ),

              const SizedBox(height: 25),

              SizedBox(
                height: 52,
                child: FilledButton(
                  onPressed: () {
                    if (!_formKey.currentState!.validate()) return;

                    final litros = double.parse(
                      _litrosController.text.replaceAll(',', '.'),
                    );

                    showDialog(
                      context: context,
                      builder: (context) => AlertDialog(
                        title: const Text('Confirmar operación'),
                        content: Text(
                          '¿Confirmas el despacho de $litros litros '
                          'para el vehículo ${vehiculo['placa']} '
                          'en la isla ${_islaController.text.trim()}?',
                        ),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.pop(context),
                            child: const Text('CANCELAR'),
                          ),
                          FilledButton(
                            onPressed: _cargando
                              ? null
                              : () async {
                                  Navigator.pop(context);
                                  await _confirmarDespacho();
                                },
                            child: const Text('CONFIRMAR'),
                          ),
                        ],
                      ),
                    );
                  },
                  style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xFF123B5D),
                  ),
                  child: const Text(
                    'CONTINUAR',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _dato(String etiqueta, dynamic valor) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        children: [
          Expanded(
            child: Text(
              etiqueta,
              style: const TextStyle(fontWeight: FontWeight.bold),
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
