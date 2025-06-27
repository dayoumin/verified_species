# Species Verifier Flutter 전환 계획

## 🎯 프로젝트 개요

**현재 상태**: Python + Tkinter (CustomTkinter) 기반 데스크톱 앱
**목표**: Flutter 기반 크로스플랫폼 앱 (모바일 + 데스크톱)

---

## 📋 현재 앱 분석

### 🏗️ 기존 아키텍처
```
species_verifier/
├── gui/                    # UI 레이어
│   ├── app.py             # 메인 앱 (2554줄)
│   ├── components/        # UI 컴포넌트들
│   └── bridge.py          # UI-비즈니스 로직 연결
├── core/                  # 비즈니스 로직
│   ├── verifier.py        # 핵심 검증 로직
│   ├── worms_api.py       # WoRMS API
│   ├── col_api.py         # COL API
│   └── external_data.py   # Wikipedia 등
├── models/                # 데이터 모델
├── utils/                 # 유틸리티
└── config.py             # 설정
```

### 🔍 핵심 기능
1. **3개 탭 시스템**: 해양생물(WoRMS), 미생물(LPSN), 통합생물(COL)
2. **검증 방식**: 직접 입력 + 파일 업로드 (Excel/CSV)
3. **API 연동**: WoRMS, LPSN, COL, Wikipedia
4. **결과 표시**: 테이블 형태, Excel 내보내기
5. **기업 네트워크 대응**: SSL 우회, 프록시 설정
6. **심층분석 시스템**: DeepSearch 기반 별도 팝업 화면 (준비 중)

---

## 🚀 단계별 전환 계획

### 📱 Phase 1: Flutter 프로젝트 초기 설정 (1-2주)

#### 1.1 환경 구축
```powershell
# Flutter 설치 및 설정
flutter doctor
flutter create species_verifier_flutter
cd species_verifier_flutter
```

#### 1.2 프로젝트 구조 설계
```
lib/
├── main.dart
├── app/
│   ├── app.dart           # 메인 앱
│   └── routes.dart        # 라우팅
├── theme/
│   ├── app_theme.dart     # 테마 설정
│   ├── app_colors.dart    # 색상 팔레트
│   └── app_text_styles.dart
├── widgets/
│   ├── common/            # 공통 컴포넌트
│   │   ├── app_button.dart
│   │   ├── app_text_field.dart
│   │   ├── app_loading.dart
│   │   └── app_tab_view.dart
│   └── species/           # 특화 컴포넌트
│       ├── results_table.dart
│       ├── verification_panel.dart
│       └── deep_search_popup.dart  # DeepSearch 팝업
├── screens/
│   ├── home_screen.dart
│   ├── marine_tab.dart
│   ├── microbe_tab.dart
│   └── col_tab.dart
├── services/              # API 서비스
│   ├── worms_service.dart
│   ├── lpsn_service.dart
│   ├── col_service.dart
│   ├── wikipedia_service.dart
│   └── deep_search_service.dart   # DeepSearch API
├── models/                # 데이터 모델
│   ├── marine_result.dart
│   ├── microbe_result.dart
│   ├── verification_result.dart
│   └── deep_search_result.dart    # DeepSearch 결과 모델
├── providers/             # 상태 관리
│   ├── verification_provider.dart
│   ├── file_provider.dart
│   └── deep_search_provider.dart  # DeepSearch 상태 관리
└── utils/
    ├── api_client.dart    # HTTP 클라이언트
    ├── file_handler.dart  # 파일 처리
    └── export_helper.dart # Excel 내보내기
```

#### 1.3 필수 패키지 설정
```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter
  
  # 상태 관리
  provider: ^6.1.1
  
  # 네트워킹
  http: ^1.1.0
  dio: ^5.4.0
  
  # 파일 처리
  file_picker: ^6.1.1
  excel: ^4.0.2
  csv: ^5.0.2
  
  # UI 라이브러리
  cupertino_icons: ^1.0.2
  flutter_spinkit: ^5.2.0
  
  # 데스크톱 지원
  window_manager: ^0.3.7
  
  # 로컬 저장소
  shared_preferences: ^2.2.2
  
  # 로깅
  logger: ^2.0.2
  
  # DeepSearch 관련
  sqflite: ^2.3.0         # 로컬 캐시 DB
  cached_network_image: ^3.3.0  # 이미지 캐싱
  url_launcher: ^6.2.2    # 외부 링크 열기

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0
```

### 🎨 Phase 2: UI 시스템 구축 (2-3주)

#### 2.1 테마 시스템 구축
```dart
// lib/theme/app_theme.dart
class AppTheme {
  static ThemeData lightTheme = ThemeData(
    primarySwatch: Colors.blue,
    colorScheme: ColorScheme.light(
      primary: Color(0xFF1976D2),  // 기존 파란색 테마 유지
      secondary: Color(0xFF424242),
      surface: Color(0xFFF5F5F5),
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: Color(0xFF1976D2),
      foregroundColor: Colors.white,
      elevation: 2,
    ),
    tabBarTheme: TabBarTheme(
      labelColor: Colors.white,
      unselectedLabelColor: Colors.white70,
      indicatorColor: Colors.white,
    ),
  );
}
```

#### 2.2 공통 컴포넌트 개발
```dart
// lib/widgets/common/app_button.dart
class AppButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final ButtonType type;
  final bool isLoading;
  
  // 기존 CustomTkinter 스타일 유지
}
```

#### 2.3 탭 레이아웃 구현
```dart
// lib/screens/home_screen.dart
class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> 
    with TickerProviderStateMixin {
  late TabController _tabController;
  
  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Icon(Icons.search),
            SizedBox(width: 8),
            Text('국립수산과학원 학명검증기 v2.0'),
          ],
        ),
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(text: '해양생물(WoRMS)'),
            Tab(text: '미생물(LPSN)'),
            Tab(text: '통합생물(COL)'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          MarineTab(),
          MicrobeTab(),
          ColTab(),
        ],
      ),
    );
  }
}
```

### 🔧 Phase 3: API 서비스 구현 (2-3주)

#### 3.1 HTTP 클라이언트 설정
```dart
// lib/utils/api_client.dart
class ApiClient {
  static final Dio _dio = Dio();
  
  static void init() {
    // 기존 Python 앱의 기업 네트워크 대응 로직 포팅
    _dio.options = BaseOptions(
      connectTimeout: Duration(seconds: 30),
      receiveTimeout: Duration(seconds: 30),
    );
    
    // SSL 우회 설정 (기업 환경 대응)
    (_dio.httpClientAdapter as DefaultHttpClientAdapter).onHttpClientCreate = (client) {
      client.badCertificateCallback = (cert, host, port) => true;
      return client;
    };
    
    // 재시도 로직
    _dio.interceptors.add(
      RetryInterceptor(
        dio: _dio,
        options: RetryOptions(
          retries: 5,
          retryInterval: Duration(milliseconds: 300),
        ),
      ),
    );
  }
  
  static Future<Response> get(String url, {Map<String, dynamic>? queryParameters}) async {
    return await _dio.get(url, queryParameters: queryParameters);
  }
}
```

#### 3.2 WoRMS API 서비스
```dart
// lib/services/worms_service.dart
class WormsService {
  static const String baseUrl = 'https://www.marinespecies.org/rest';
  
  static Future<Map<String, dynamic>?> getAphiaId(String scientificName) async {
    try {
      final response = await ApiClient.get(
        '$baseUrl/AphiaIDByName/${Uri.encodeComponent(scientificName)}',
        queryParameters: {'marine_only': false},
      );
      
      if (response.statusCode == 200) {
        return {'aphia_id': response.data};
      } else if (response.statusCode == 204) {
        return {'error': 'WoRMS 응답 없음'};
      }
    } catch (e) {
      return {'error': '네트워크 오류: $e'};
    }
    return null;
  }
  
  static Future<Map<String, dynamic>?> getAphiaRecord(int aphiaId) async {
    // 기존 Python 로직 포팅
  }
  
  static Future<List<VerificationResult>> verifySpeciesList(
    List<String> species, 
    Function(double)? onProgress
  ) async {
    // 기존 검증 로직 포팅
  }
}
```

#### 3.3 상태 관리 구현
```dart
// lib/providers/verification_provider.dart
class VerificationProvider extends ChangeNotifier {
  List<VerificationResult> _results = [];
  bool _isLoading = false;
  double _progress = 0.0;
  String _statusMessage = '';
  
  List<VerificationResult> get results => _results;
  bool get isLoading => _isLoading;
  double get progress => _progress;
  String get statusMessage => _statusMessage;
  
  Future<void> verifySpecies(List<String> species, String apiType) async {
    _isLoading = true;
    _progress = 0.0;
    _results.clear();
    notifyListeners();
    
    try {
      switch (apiType) {
        case 'worms':
          _results = await WormsService.verifySpeciesList(
            species,
            (progress) {
              _progress = progress;
              notifyListeners();
            },
          );
          break;
        case 'lpsn':
          // LPSN 검증 로직
          break;
        case 'col':
          // COL 검증 로직
          break;
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
```

### 📱 Phase 4: 탭별 기능 구현 (3-4주)

#### 4.1 해양생물 탭
```dart
// lib/screens/marine_tab.dart
class MarineTab extends StatefulWidget {
  @override
  _MarineTabState createState() => _MarineTabState();
}

class _MarineTabState extends State<MarineTab> {
  final TextEditingController _textController = TextEditingController();
  
  @override
  Widget build(BuildContext context) {
    return Consumer<VerificationProvider>(
      builder: (context, provider, child) {
        return Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 직접 입력 섹션
              Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.edit, color: AppColors.primary),
                          SizedBox(width: 8),
                          Text('직접 입력', style: AppTextStyles.heading2),
                        ],
                      ),
                      SizedBox(height: 12),
                      AppTextField(
                        controller: _textController,
                        hintText: '여러 학명은 콤마로 구분 (예: Paralichthys olivaceus, Anguilla japonica)',
                        maxLines: 3,
                      ),
                    ],
                  ),
                ),
              ),
              
              SizedBox(height: 16),
              
              // 파일 입력 섹션
              Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.file_upload, color: AppColors.primary),
                          SizedBox(width: 8),
                          Text('파일 입력', style: AppTextStyles.heading2),
                        ],
                      ),
                      SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: AppTextField(
                              hintText: '파일을 선택하세요 (.xlsx, .csv)',
                              readOnly: true,
                            ),
                          ),
                          SizedBox(width: 8),
                          AppButton(
                            text: '찾기',
                            onPressed: _pickFile,
                          ),
                          SizedBox(width: 8),
                          AppButton(
                            text: '자유기',
                            onPressed: _clearFile,
                            type: ButtonType.secondary,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              
              SizedBox(height: 16),
              
              // 검증 시작 버튼
              Center(
                child: AppButton(
                  text: '🔍 검증 시작',
                  onPressed: provider.isLoading ? null : _startVerification,
                  isLoading: provider.isLoading,
                ),
              ),
              
              SizedBox(height: 16),
              
              // 진행률 표시
              if (provider.isLoading) ...[
                LinearProgressIndicator(value: provider.progress),
                SizedBox(height: 8),
                Text(provider.statusMessage, style: AppTextStyles.body),
                SizedBox(height: 16),
              ],
              
              // 결과 테이블
              Expanded(
                child: ResultsTable(
                  results: provider.results,
                  onExport: _exportResults,
                  onDeepSearchRequested: _showDeepSearchPopup,  // DeepSearch 팝업 호출
                ),
              ),
            ],
          ),
        );
      },
    );
  }
  
  // DeepSearch 팝업 표시
  void _showDeepSearchPopup(String scientificName) {
    showDialog(
      context: context,
      builder: (context) => DeepSearchPopup(scientificName: scientificName),
    );
  }
}
```

#### 4.2 결과 테이블 컴포넌트
```dart
// lib/widgets/species/results_table.dart
class ResultsTable extends StatelessWidget {
  final List<VerificationResult> results;
  final VoidCallback? onExport;
  
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 헤더
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.vertical(top: Radius.circular(8)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('검증 결과 ${results.length}개', style: AppTextStyles.heading2),
                if (results.isNotEmpty)
                  AppButton(
                    text: '📊 Excel 저장',
                    onPressed: onExport,
                    type: ButtonType.success,
                  ),
              ],
            ),
          ),
          
          // 테이블
          Expanded(
            child: SingleChildScrollView(
              child: DataTable(
                columns: [
                  DataColumn(label: Text('학명')),
                  DataColumn(label: Text('검증')),
                  DataColumn(label: Text('WoRMS 상태')),
                  DataColumn(label: Text('WoRMS ID')),
                  DataColumn(label: Text('WoRMS URL')),
                  DataColumn(label: Text('실용분류 결과')),
                ],
                rows: results.map((result) {
                  return DataRow(
                    cells: [
                      DataCell(Text(result.scientificName)),
                      DataCell(
                        Container(
                          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: result.isVerified ? AppColors.success : AppColors.error,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            result.isVerified ? '✓' : '✗',
                            style: TextStyle(color: Colors.white),
                          ),
                        ),
                      ),
                      DataCell(Text(result.wormsStatus)),
                      DataCell(Text(result.wormsId.toString())),
                      DataCell(
                        result.wormsUrl.isNotEmpty
                          ? InkWell(
                              onTap: () => _launchUrl(result.wormsUrl),
                              child: Text('보기', style: TextStyle(color: AppColors.primary)),
                            )
                          : Text('-'),
                      ),
                      DataCell(Text(result.taxonomyResult)),
                    ],
                  );
                }).toList(),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
```

### 📱 Phase 5: 파일 처리 및 내보내기 (1-2주)

#### 5.1 파일 처리 서비스
```dart
// lib/utils/file_handler.dart
class FileHandler {
  static Future<List<String>?> pickAndReadFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['xlsx', 'csv'],
      );
      
      if (result != null) {
        final file = result.files.first;
        if (file.extension == 'xlsx') {
          return _readExcelFile(file.bytes!);
        } else if (file.extension == 'csv') {
          return _readCsvFile(file.bytes!);
        }
      }
    } catch (e) {
      print('파일 읽기 오류: $e');
    }
    return null;
  }
  
  static List<String> _readExcelFile(Uint8List bytes) {
    final excel = Excel.decodeBytes(bytes);
    final sheet = excel.tables.values.first;
    final names = <String>[];
    
    for (final row in sheet.rows.skip(1)) { // 헤더 스킵
      if (row.isNotEmpty && row.first?.value != null) {
        names.add(row.first!.value.toString().trim());
      }
    }
    
    return names;
  }
  
  static List<String> _readCsvFile(Uint8List bytes) {
    final content = utf8.decode(bytes);
    final rows = CsvToListConverter().convert(content);
    final names = <String>[];
    
    for (final row in rows.skip(1)) { // 헤더 스킵
      if (row.isNotEmpty && row.first != null) {
        names.add(row.first.toString().trim());
      }
    }
    
    return names;
  }
}
```

#### 5.2 Excel 내보내기
```dart
// lib/utils/export_helper.dart
class ExportHelper {
  static Future<void> exportToExcel(List<VerificationResult> results, String tabType) async {
    final excel = Excel.createExcel();
    final sheet = excel['결과'];
    
    // 헤더 추가
    final headers = ['학명', '검증', 'WoRMS 상태', 'WoRMS ID', 'WoRMS URL', '실용분류 결과'];
    for (int i = 0; i < headers.length; i++) {
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: i, rowIndex: 0)).value = headers[i];
    }
    
    // 데이터 추가
    for (int i = 0; i < results.length; i++) {
      final result = results[i];
      final row = i + 1;
      
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 0, rowIndex: row)).value = result.scientificName;
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 1, rowIndex: row)).value = result.isVerified ? '✓' : '✗';
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 2, rowIndex: row)).value = result.wormsStatus;
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 3, rowIndex: row)).value = result.wormsId.toString();
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 4, rowIndex: row)).value = result.wormsUrl;
      sheet.cell(CellIndex.indexByColumnRow(columnIndex: 5, rowIndex: row)).value = result.taxonomyResult;
    }
    
    // 파일 저장
    final fileName = 'species_verification_${tabType}_${DateTime.now().millisecondsSinceEpoch}.xlsx';
    final bytes = excel.encode()!;
    
    // 플랫폼별 저장 로직
    if (Platform.isWindows || Platform.isLinux || Platform.isMacOS) {
      final result = await FilePicker.platform.saveFile(
        dialogTitle: 'Excel 파일 저장',
        fileName: fileName,
        type: FileType.custom,
        allowedExtensions: ['xlsx'],
      );
      
      if (result != null) {
        final file = File(result);
        await file.writeAsBytes(bytes);
      }
    } else {
      // 모바일 플랫폼에서는 다운로드 폴더에 저장
      final directory = await getExternalStorageDirectory();
      final file = File('${directory!.path}/$fileName');
      await file.writeAsBytes(bytes);
    }
  }
}
```

### 🎨 Phase 6: 고급 기능 및 최적화 (2-3주)

#### 6.1 반응형 디자인
```dart
// lib/utils/responsive.dart
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget tablet;
  final Widget desktop;
  
  const ResponsiveLayout({
    required this.mobile,
    required this.tablet,
    required this.desktop,
  });
  
  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 768) {
          return mobile;
        } else if (constraints.maxWidth < 1024) {
          return tablet;
        } else {
          return desktop;
        }
      },
    );
  }
}
```

#### 6.2 로컬 데이터 캐싱
```dart
// lib/services/cache_service.dart
class CacheService {
  static const String _cacheKey = 'verification_cache';
  
  static Future<void> saveResults(String key, List<VerificationResult> results) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = jsonEncode(results.map((r) => r.toJson()).toList());
    await prefs.setString('${_cacheKey}_$key', jsonString);
  }
  
  static Future<List<VerificationResult>?> loadResults(String key) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString('${_cacheKey}_$key');
    
    if (jsonString != null) {
      final jsonList = jsonDecode(jsonString) as List;
      return jsonList.map((json) => VerificationResult.fromJson(json)).toList();
    }
    
    return null;
  }
}
```

### 📱 Phase 7: 테스트 및 배포 (1-2주)

#### 7.1 단위 테스트
```dart
// test/services/worms_service_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:species_verifier_flutter/services/worms_service.dart';

void main() {
  group('WormsService Tests', () {
    test('getAphiaId should return valid ID for known species', () async {
      final result = await WormsService.getAphiaId('Homo sapiens');
      expect(result, isNotNull);
      expect(result!['aphia_id'], isA<int>());
    });
    
    test('getAphiaId should return error for unknown species', () async {
      final result = await WormsService.getAphiaId('Unknown species');
      expect(result, isNotNull);
      expect(result!['error'], isNotNull);
    });
  });
}
```

#### 7.2 통합 테스트
```dart
// integration_test/app_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:species_verifier_flutter/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  
  group('Species Verifier App Tests', () {
    testWidgets('Full verification workflow', (tester) async {
      app.main();
      await tester.pumpAndSettle();
      
      // 1. 메인 화면 로드 확인
      expect(find.text('국립수산과학원 학명검증기'), findsOneWidget);
      
      // 2. 해양생물 탭에서 학명 입력
      await tester.tap(find.text('해양생물(WoRMS)'));
      await tester.pumpAndSettle();
      
      await tester.enterText(
        find.byType(TextField),
        'Paralichthys olivaceus',
      );
      
      // 3. 검증 시작
      await tester.tap(find.text('🔍 검증 시작'));
      await tester.pumpAndSettle();
      
      // 4. 결과 확인 (최대 30초 대기)
      await tester.pumpAndSettle(Duration(seconds: 30));
      expect(find.text('검증 결과'), findsOneWidget);
    });
  });
}
```

#### 7.3 빌드 및 배포
```powershell
# Windows 데스크톱 빌드
flutter build windows --release

# Android APK 빌드
flutter build apk --release

# iOS 빌드 (macOS에서)
flutter build ios --release

# 웹 빌드
flutter build web --release
```

---

## 📋 마이그레이션 체크리스트

### ✅ Phase 1 완료 조건
- [ ] Flutter 프로젝트 생성 및 폴더 구조 설정
- [ ] 필수 패키지 설치 및 설정
- [ ] 기본 테마 시스템 구축
- [ ] 공통 컴포넌트 (버튼, 입력 필드) 구현

### ✅ Phase 2 완료 조건
- [ ] 3개 탭 레이아웃 구현
- [ ] 기존 UI와 90% 이상 유사한 디자인
- [ ] 반응형 레이아웃 적용
- [ ] 상태 관리 Provider 설정

### ✅ Phase 3 완료 조건
- [ ] WoRMS API 서비스 구현 및 테스트
- [ ] LPSN API 서비스 구현 및 테스트
- [ ] COL API 서비스 구현 및 테스트
- [ ] 기업 네트워크 대응 (SSL 우회) 구현

### ✅ Phase 4 완료 조건
- [ ] 해양생물 탭 완전 구현
- [ ] 미생물 탭 완전 구현
- [ ] 통합생물 탭 완전 구현
- [ ] 검증 로직 100% 포팅

### ✅ Phase 5 완료 조건
- [ ] 파일 업로드 (Excel/CSV) 기능
- [ ] 결과 Excel 내보내기 기능
- [ ] 파일 처리 에러 핸들링

### ✅ Phase 6 완료 조건
- [ ] 성능 최적화 (대량 데이터 처리)
- [ ] 로컬 캐싱 구현
- [ ] 데스크톱/모바일 UI 최적화

### ✅ Phase 7 완료 조건 (DeepSearch 시스템)
- [ ] DeepSearch 팝업 화면 구현 (탭 기반)
- [ ] Supabase 연동 및 데이터 캐싱
- [ ] 위키피디아 및 다중 소스 데이터 수집
- [ ] 이미지 갤러리 및 참고문헌 링크 기능
- [ ] "준비 중" 메시지를 실제 기능으로 대체

### ✅ Phase 8 완료 조건
- [ ] 단위 테스트 90% 이상 커버리지
- [ ] 통합 테스트 완료
- [ ] Windows/Android/Web 빌드 성공

---

## 🚀 권장 학습 순서

### 1단계: Flutter 기초 (1주)
- **Dart 언어 기초**: 변수, 함수, 클래스, async/await
- **Flutter 위젯**: StatelessWidget, StatefulWidget, 기본 위젯들
- **레이아웃**: Column, Row, Container, Scaffold

### 2단계: 상태 관리 (1주)
- **Provider 패턴**: ChangeNotifier, Consumer, Provider
- **상태 전파**: notifyListeners(), rebuild 메커니즘

### 3단계: 네트워킹 (1주)
- **HTTP 통신**: Dio 패키지, GET/POST 요청
- **JSON 처리**: Map<String, dynamic>, fromJson/toJson
- **에러 핸들링**: try-catch, Future 에러 처리

### 4단계: 실전 적용 (나머지)
- **현재 프로젝트 포팅**: 기존 Python 로직을 Dart로 변환
- **점진적 개선**: 탭별로 하나씩 완성

---

## 💡 마이그레이션 팁

### 🔄 Python → Dart 변환 가이드
```python
# Python (기존)
def verify_species_list(species_list):
    results = []
    for species in species_list:
        result = check_worms_record(species)
        results.append(result)
    return results
```

```dart
// Dart (변환)
Future<List<VerificationResult>> verifySpeciesList(List<String> speciesList) async {
  final results = <VerificationResult>[];
  for (final species in speciesList) {
    final result = await checkWormsRecord(species);
    results.add(result);
  }
  return results;
}
```

### 🎯 핵심 포인트
1. **점진적 전환**: 한 번에 모든 것을 바꾸지 말고 탭별로 단계적 구현
2. **기존 API 로직 유지**: 검증된 비즈니스 로직은 최대한 그대로 포팅
3. **사용자 경험 우선**: 기존 사용자가 혼란스럽지 않도록 UI/UX 유지
4. **성능 고려**: 대량 데이터 처리 시 async/await와 Stream 활용

### 🔧 개발 환경 권장사항
- **IDE**: VS Code + Flutter extension
- **디버깅**: Flutter Inspector, Dart DevTools
- **버전 관리**: Git branch 전략 (feature/phase1, feature/phase2...)
- **테스트**: 각 Phase 완료 시마다 기능 테스트

---

## 🎯 최종 목표

### 📱 Flutter 버전 장점
1. **크로스 플랫폼**: Windows + Android + iOS + Web
2. **현대적 UI**: Material Design 3.0 적용
3. **성능 향상**: 네이티브 수준 성능
4. **유지보수성**: 더 깔끔한 코드 구조
5. **확장성**: 모바일 중심의 미래 지향적 설계

### 🚀 장기 비전
- **모바일 버전**: 현장에서 즉시 학명 검증
- **오프라인 모드**: 캐시된 데이터로 오프라인 검증
- **클라우드 연동**: 사용자별 검증 히스토리 관리
- **AI 기능**: 이미지 기반 종 식별 기능 추가

**이 계획대로 진행하면 약 12-14주 내에 DeepSearch 기능을 포함한 완전한 Flutter 버전을 완성할 수 있습니다!** 🎯

---

## 🔍 DeepSearch 팝업 구현 예시

### DeepSearch 팝업 컴포넌트
```dart
// lib/widgets/species/deep_search_popup.dart
class DeepSearchPopup extends StatefulWidget {
  final String scientificName;
  
  const DeepSearchPopup({Key? key, required this.scientificName}) : super(key: key);
  
  @override
  _DeepSearchPopupState createState() => _DeepSearchPopupState();
}

class _DeepSearchPopupState extends State<DeepSearchPopup> 
    with TickerProviderStateMixin {
  late TabController _tabController;
  DeepSearchResult? _result;
  bool _isLoading = true;
  
  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 8, vsync: this);
    _loadDeepSearchData();
  }
  
  Future<void> _loadDeepSearchData() async {
    try {
      final result = await DeepSearchService.getDetailedInfo(widget.scientificName);
      setState(() {
        _result = result;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      // 에러 처리
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Container(
        width: MediaQuery.of(context).size.width * 0.9,
        height: MediaQuery.of(context).size.height * 0.8,
        child: Column(
          children: [
            // 헤더
            Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.vertical(top: Radius.circular(8)),
              ),
              child: Row(
                children: [
                  Icon(Icons.info_outline, color: Colors.white),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '종정보: ${widget.scientificName}',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  IconButton(
                    icon: Icon(Icons.close, color: Colors.white),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),
            
            // 탭 바
            if (!_isLoading && _result != null)
              Container(
                color: AppColors.surface,
                child: TabBar(
                  controller: _tabController,
                  isScrollable: true,
                  labelColor: AppColors.primary,
                  unselectedLabelColor: Colors.grey,
                  tabs: [
                    Tab(text: '개요'),
                    Tab(text: '분류학'),
                    Tab(text: '생태학'),
                    Tab(text: '형태학'),
                    Tab(text: '분포/서식지'),
                    Tab(text: '보전/경제'),
                    Tab(text: '이미지'),
                    Tab(text: '참고문헌'),
                  ],
                ),
              ),
            
            // 탭 내용
            Expanded(
              child: _isLoading
                  ? Center(child: CircularProgressIndicator())
                  : _result == null
                      ? Center(child: Text('데이터를 불러올 수 없습니다.'))
                      : TabBarView(
                          controller: _tabController,
                          children: [
                            _buildOverviewTab(),
                            _buildTaxonomyTab(),
                            _buildEcologyTab(),
                            _buildMorphologyTab(),
                            _buildDistributionTab(),
                            _buildConservationTab(),
                            _buildImageGalleryTab(),
                            _buildReferencesTab(),
                          ],
                        ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildOverviewTab() {
    return Padding(
      padding: EdgeInsets.all(16),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('개요', style: AppTextStyles.heading1),
            SizedBox(height: 16),
            if (_result!.koreanName.isNotEmpty) ...[
              Text('국명: ${_result!.koreanName}', style: AppTextStyles.body),
              SizedBox(height: 8),
            ],
            Text('학명: ${widget.scientificName}', style: AppTextStyles.body),
            SizedBox(height: 16),
            if (_result!.summary.isNotEmpty) ...[
              Text('요약', style: AppTextStyles.heading2),
              SizedBox(height: 8),
              Text(_result!.summary, style: AppTextStyles.body),
            ],
          ],
        ),
      ),
    );
  }
  
  Widget _buildImageGalleryTab() {
    return Padding(
      padding: EdgeInsets.all(16),
      child: _result!.images.isEmpty
          ? Center(child: Text('이미지가 없습니다.'))
          : GridView.builder(
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 8,
                mainAxisSpacing: 8,
              ),
              itemCount: _result!.images.length,
              itemBuilder: (context, index) {
                return CachedNetworkImage(
                  imageUrl: _result!.images[index],
                  placeholder: (context, url) => 
                      Center(child: CircularProgressIndicator()),
                  errorWidget: (context, url, error) => 
                      Icon(Icons.error),
                  fit: BoxFit.cover,
                );
              },
            ),
    );
  }
  
  Widget _buildReferencesTab() {
    return Padding(
      padding: EdgeInsets.all(16),
      child: _result!.references.isEmpty
          ? Center(child: Text('참고문헌이 없습니다.'))
          : ListView.builder(
              itemCount: _result!.references.length,
              itemBuilder: (context, index) {
                final ref = _result!.references[index];
                return Card(
                  margin: EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    title: Text(ref.title),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (ref.authors.isNotEmpty)
                          Text('저자: ${ref.authors}'),
                        if (ref.journal.isNotEmpty)
                          Text('저널: ${ref.journal}'),
                        if (ref.year > 0)
                          Text('연도: ${ref.year}'),
                      ],
                    ),
                    trailing: ref.url.isNotEmpty
                        ? IconButton(
                            icon: Icon(Icons.open_in_new),
                            onPressed: () => _launchURL(ref.url),
                          )
                        : null,
                  ),
                );
              },
            ),
    );
  }
  
  void _launchURL(String url) async {
    if (await canLaunch(url)) {
      await launch(url);
    }
  }
  
  // 다른 탭들 구현...
}
```

### DeepSearch 서비스
```dart
// lib/services/deep_search_service.dart
class DeepSearchService {
  static Future<DeepSearchResult?> getDetailedInfo(String scientificName) async {
    try {
      // 1. 캐시 확인
      final cached = await _getCachedResult(scientificName);
      if (cached != null && !_isCacheExpired(cached)) {
        return cached;
      }
      
      // 2. 다중 소스에서 데이터 수집
      final futures = [
        _getWikipediaData(scientificName),
        _getEOLData(scientificName),
        _getGBIFData(scientificName),
      ];
      
      final results = await Future.wait(futures);
      
      // 3. 데이터 통합
      final result = _aggregateData(results, scientificName);
      
      // 4. 캐시 저장
      await _saveCachedResult(result);
      
      return result;
    } catch (e) {
      print('DeepSearch error: $e');
      return null;
    }
  }
  
  // 다른 메서드들...
}
```

### DeepSearch 결과 모델
```dart
// lib/models/deep_search_result.dart
class DeepSearchResult {
  final String scientificName;
  final String koreanName;
  final String summary;
  final Map<String, dynamic> taxonomy;
  final Map<String, dynamic> ecology;
  final String morphology;
  final String distribution;
  final String conservationStatus;
  final String economicImportance;
  final List<String> images;
  final List<Reference> references;
  final DateTime lastUpdated;
  
  DeepSearchResult({
    required this.scientificName,
    required this.koreanName,
    required this.summary,
    required this.taxonomy,
    required this.ecology,
    required this.morphology,
    required this.distribution,
    required this.conservationStatus,
    required this.economicImportance,
    required this.images,
    required this.references,
    required this.lastUpdated,
  });
  
  factory DeepSearchResult.fromJson(Map<String, dynamic> json) {
    return DeepSearchResult(
      scientificName: json['scientific_name'] ?? '',
      koreanName: json['korean_name'] ?? '',
      summary: json['summary'] ?? '',
      taxonomy: json['taxonomy'] ?? {},
      ecology: json['ecology'] ?? {},
      morphology: json['morphology'] ?? '',
      distribution: json['distribution'] ?? '',
      conservationStatus: json['conservation_status'] ?? '',
      economicImportance: json['economic_importance'] ?? '',
      images: List<String>.from(json['images'] ?? []),
      references: (json['references'] as List<dynamic>?)
          ?.map((e) => Reference.fromJson(e))
          .toList() ?? [],
      lastUpdated: DateTime.parse(json['last_updated'] ?? DateTime.now().toIso8601String()),
    );
  }
}

class Reference {
  final String title;
  final String authors;
  final String journal;
  final int year;
  final String url;
  
  Reference({
    required this.title,
    required this.authors,
    required this.journal,
    required this.year,
    required this.url,
  });
  
  factory Reference.fromJson(Map<String, dynamic> json) {
    return Reference(
      title: json['title'] ?? '',
      authors: json['authors'] ?? '',
      journal: json['journal'] ?? '',
      year: json['year'] ?? 0,
      url: json['url'] ?? '',
    );
  }
}
```

이제 DeepSearch 기능이 포함된 완전한 Flutter 전환 계획이 완성되었습니다! 🚀 