
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../config/api_config.dart';
import 'api_service.dart';

class AuthService {
  final ApiService _api = ApiService();

  final FlutterSecureStorage _storage =
      const FlutterSecureStorage();

  Future<Map<String, dynamic>> iniciarSesion({
    required String email,
    required String password,
  }) async {
    final respuesta = await _api.post(
      ApiConfig.loginEndpoint,
      {
        'email': email.trim().toLowerCase(),
        'password': password,
      },
    );

    final token = respuesta['access_token'];
    final usuario = respuesta['usuario'];

    if (token is! String ||
        token.isEmpty ||
        usuario is! Map) {
      throw Exception('Respuesta de autenticación incompleta.');
    }

    final datosUsuario = Map<String, dynamic>.from(usuario);

    final rol = datosUsuario['rol'];

    if (rol != 'DESPACHADOR') {
      throw Exception(
        'Acceso denegado. Esta aplicación es exclusiva para despachadores.',
      );
    }

    await _storage.write(
      key: 'access_token',
      value: token,
    );

    return datosUsuario;
  }

  Future<Map<String, dynamic>> obtenerPerfil() async {
    final token = await _storage.read(key: 'access_token');

    if (token == null || token.isEmpty) {
      throw Exception('No existe una sesión activa.');
    }

    final respuesta = await _api.get(
      ApiConfig.meEndpoint,
      token: token,
    );

    if (respuesta['rol'] != 'DESPACHADOR') {
      await cerrarSesion();
      throw Exception('El usuario no tiene permiso para esta aplicación.');
    }

    return respuesta;
  }

  Future<void> cerrarSesion() async {
    await _storage.delete(key: 'access_token');
  }
}
