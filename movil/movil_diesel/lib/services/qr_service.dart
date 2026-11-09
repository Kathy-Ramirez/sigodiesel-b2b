
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'api_service.dart';

class QrService {
  final ApiService _api = ApiService();

  final FlutterSecureStorage _storage =
      const FlutterSecureStorage();

  Future<Map<String, dynamic>> validarQr(String tokenQr) async {
    final token = await _storage.read(key: 'access_token');

    if (token == null || token.isEmpty) {
      throw Exception('No existe una sesión activa. Inicia sesión nuevamente.');
    }

    final respuesta = await _api.get(
      '/despachos/validar-qr/${Uri.encodeComponent(tokenQr)}',
      token: token,
    );

    return respuesta;
  }
}
