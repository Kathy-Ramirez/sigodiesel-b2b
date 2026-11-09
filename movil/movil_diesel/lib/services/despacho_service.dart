
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'api_service.dart';

class DespachoService {
  final ApiService _api = ApiService();

  final FlutterSecureStorage _storage =
      const FlutterSecureStorage();

  Future<Map<String, dynamic>> registrarDespacho({
    required String tokenQr,
    required double litrosCargados,
    required String nroIsla,
    required String idOperacion,
  }) async {
    final token = await _storage.read(key: 'access_token');

    if (token == null || token.isEmpty) {
      throw Exception('No existe una sesión activa.');
    }

    return await _api.post(
      '/despachos/registrar',
      {
        'token_qr': tokenQr,
        'litros_cargados': litrosCargados,
        'nro_isla': nroIsla,
        'id_operacion': idOperacion,
      },
      token: token,
    );
  }
}
