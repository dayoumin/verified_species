# Flutter UI 개발 완전 가이드

## 🎯 핵심 교훈
**"처음 30분 투자로 나중에 5-10시간 절약"**

공통 스타일 시스템을 먼저 구축하고, 라이브러리 특성을 미리 파악하며, 확장 가능한 컴포넌트 구조를 설계하는 것이 성공의 열쇠입니다.

---

## 📋 Flutter UI 개발 체크리스트

### 🎨 1. 스타일 시스템 구축 (최우선)
- [ ] **앱 테마 정의** (`ThemeData` 설정)
  ```dart
  // lib/theme/app_theme.dart
  class AppTheme {
    static ThemeData lightTheme = ThemeData(
      primarySwatch: Colors.blue,
      colorScheme: ColorScheme.light(
        primary: Color(0xFF1976D2),
        secondary: Color(0xFF424242),
        surface: Color(0xFFF5F5F5),
      ),
      textTheme: TextTheme(
        headlineLarge: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        bodyLarge: TextStyle(fontSize: 16, color: Colors.black87),
      ),
    );
  }
  ```

- [ ] **공통 색상 팔레트** (`AppColors` 클래스)
  ```dart
  // lib/theme/app_colors.dart
  class AppColors {
    static const Color primary = Color(0xFF1976D2);
    static const Color secondary = Color(0xFF424242);
    static const Color success = Color(0xFF4CAF50);
    static const Color warning = Color(0xFFFF9800);
    static const Color error = Color(0xFFF44336);
    static const Color surface = Color(0xFFF5F5F5);
    static const Color background = Color(0xFFFFFFFF);
    
    // 버튼 색상
    static const Color buttonPrimary = primary;
    static const Color buttonSecondary = secondary;
    static const Color buttonText = Colors.white;
    static const Color buttonTextDisabled = Color(0xFF9E9E9E);
  }
  ```

- [ ] **텍스트 스타일** (`AppTextStyles` 클래스)
  ```dart
  // lib/theme/app_text_styles.dart
  class AppTextStyles {
    static const TextStyle heading1 = TextStyle(
      fontSize: 24,
      fontWeight: FontWeight.bold,
      color: AppColors.primary,
    );
    
    static const TextStyle heading2 = TextStyle(
      fontSize: 20,
      fontWeight: FontWeight.w600,
      color: AppColors.secondary,
    );
    
    static const TextStyle body = TextStyle(
      fontSize: 16,
      color: Colors.black87,
    );
    
    static const TextStyle buttonText = TextStyle(
      fontSize: 16,
      fontWeight: FontWeight.w500,
      color: AppColors.buttonText,
    );
  }
  ```

### 🧩 2. 공통 컴포넌트 개발
- [ ] **기본 버튼 컴포넌트**
  ```dart
  // lib/widgets/common/app_button.dart
  class AppButton extends StatelessWidget {
    final String text;
    final VoidCallback? onPressed;
    final ButtonType type;
    final bool isLoading;
    
    const AppButton({
      Key? key,
      required this.text,
      this.onPressed,
      this.type = ButtonType.primary,
      this.isLoading = false,
    }) : super(key: key);
    
    @override
    Widget build(BuildContext context) {
      return ElevatedButton(
        onPressed: isLoading ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: _getBackgroundColor(),
          foregroundColor: AppColors.buttonText,
          disabledBackgroundColor: Colors.grey[300],
          disabledForegroundColor: AppColors.buttonTextDisabled,
          padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
        child: isLoading 
          ? SizedBox(
              height: 20,
              width: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(AppColors.buttonText),
              ),
            )
          : Text(text, style: AppTextStyles.buttonText),
      );
    }
    
    Color _getBackgroundColor() {
      switch (type) {
        case ButtonType.primary:
          return AppColors.buttonPrimary;
        case ButtonType.secondary:
          return AppColors.buttonSecondary;
        case ButtonType.success:
          return AppColors.success;
        case ButtonType.warning:
          return AppColors.warning;
        case ButtonType.error:
          return AppColors.error;
      }
    }
  }
  
  enum ButtonType { primary, secondary, success, warning, error }
  ```

- [ ] **공통 입력 필드**
  ```dart
  // lib/widgets/common/app_text_field.dart
  class AppTextField extends StatelessWidget {
    final String? labelText;
    final String? hintText;
    final TextEditingController? controller;
    final ValueChanged<String>? onChanged;
    final String? Function(String?)? validator;
    final bool obscureText;
    final int? maxLines;
    
    const AppTextField({
      Key? key,
      this.labelText,
      this.hintText,
      this.controller,
      this.onChanged,
      this.validator,
      this.obscureText = false,
      this.maxLines = 1,
    }) : super(key: key);
    
    @override
    Widget build(BuildContext context) {
      return TextFormField(
        controller: controller,
        onChanged: onChanged,
        validator: validator,
        obscureText: obscureText,
        maxLines: maxLines,
        style: AppTextStyles.body,
        decoration: InputDecoration(
          labelText: labelText,
          hintText: hintText,
          labelStyle: AppTextStyles.body.copyWith(color: AppColors.secondary),
          hintStyle: AppTextStyles.body.copyWith(color: Colors.grey[600]),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide(color: Colors.grey[400]!),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide(color: AppColors.primary, width: 2),
          ),
          errorBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide(color: AppColors.error, width: 2),
          ),
          contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        ),
      );
    }
  }
  ```

- [ ] **로딩 인디케이터**
  ```dart
  // lib/widgets/common/app_loading.dart
  class AppLoading extends StatelessWidget {
    final String? message;
    final bool overlay;
    
    const AppLoading({
      Key? key,
      this.message,
      this.overlay = false,
    }) : super(key: key);
    
    @override
    Widget build(BuildContext context) {
      final content = Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
          ),
          if (message != null) ...[
            SizedBox(height: 16),
            Text(message!, style: AppTextStyles.body),
          ],
        ],
      );
      
      if (overlay) {
        return Container(
          color: Colors.black54,
          child: Center(child: content),
        );
      }
      
      return Center(child: content);
    }
  }
  ```

### 📱 3. 레이아웃 시스템
- [ ] **반응형 레이아웃**
  ```dart
  // lib/utils/responsive.dart
  class Responsive {
    static bool isMobile(BuildContext context) =>
        MediaQuery.of(context).size.width < 768;
    
    static bool isTablet(BuildContext context) =>
        MediaQuery.of(context).size.width >= 768 &&
        MediaQuery.of(context).size.width < 1024;
    
    static bool isDesktop(BuildContext context) =>
        MediaQuery.of(context).size.width >= 1024;
    
    static double screenWidth(BuildContext context) =>
        MediaQuery.of(context).size.width;
    
    static double screenHeight(BuildContext context) =>
        MediaQuery.of(context).size.height;
  }
  ```

- [ ] **공통 패딩/마진**
  ```dart
  // lib/constants/app_spacing.dart
  class AppSpacing {
    static const double xs = 4.0;
    static const double sm = 8.0;
    static const double md = 16.0;
    static const double lg = 24.0;
    static const double xl = 32.0;
    static const double xxl = 48.0;
  }
  ```

### 🏗️ 4. 상태 관리 준비
- [ ] **Provider/Riverpod/Bloc 설정**
- [ ] **전역 상태 구조 설계**
- [ ] **로컬 상태 vs 전역 상태 분리**

### 🎯 5. 네비게이션 구조
- [ ] **라우팅 시스템 설정** (GoRouter 권장)
- [ ] **네비게이션 가드**
- [ ] **딥링크 대응**

---

## 🛠️ Flutter 위젯별 주의사항

### CustomScrollView & Slivers
```dart
// 올바른 스크롤 뷰 구성
CustomScrollView(
  slivers: [
    SliverAppBar(
      pinned: true,
      backgroundColor: AppColors.primary,
      title: Text('앱 제목', style: AppTextStyles.heading1),
    ),
    SliverPadding(
      padding: EdgeInsets.all(AppSpacing.md),
      sliver: SliverList(
        delegate: SliverChildBuilderDelegate(
          (context, index) => _buildListItem(index),
          childCount: itemCount,
        ),
      ),
    ),
  ],
)
```

### ListView.builder 최적화
```dart
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    return ListTile(
      title: Text(items[index].title, style: AppTextStyles.body),
      subtitle: Text(items[index].subtitle),
      tileColor: index.isEven ? AppColors.surface : null,
    );
  },
)
```

### Form 유효성 검사
```dart
class FormScreen extends StatefulWidget {
  @override
  _FormScreenState createState() => _FormScreenState();
}

class _FormScreenState extends State<FormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  
  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        children: [
          AppTextField(
            controller: _emailController,
            labelText: '이메일',
            validator: (value) {
              if (value?.isEmpty ?? true) return '이메일을 입력하세요';
              if (!value!.contains('@')) return '올바른 이메일을 입력하세요';
              return null;
            },
          ),
          AppButton(
            text: '제출',
            onPressed: () {
              if (_formKey.currentState!.validate()) {
                // 폼 제출 로직
              }
            },
          ),
        ],
      ),
    );
  }
}
```

---

## 🎨 고급 UI 패턴

### 1. 탭 기반 레이아웃
```dart
class TabScreen extends StatefulWidget {
  @override
  _TabScreenState createState() => _TabScreenState();
}

class _TabScreenState extends State<TabScreen> with TickerProviderStateMixin {
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
        backgroundColor: AppColors.primary,
        title: Text('앱 제목', style: AppTextStyles.heading1),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppColors.buttonText,
          labelStyle: AppTextStyles.buttonText,
          tabs: [
            Tab(text: '탭 1'),
            Tab(text: '탭 2'),
            Tab(text: '탭 3'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildTab1(),
          _buildTab2(),
          _buildTab3(),
        ],
      ),
    );
  }
}
```

### 2. 검색 기능이 있는 리스트
```dart
class SearchableList extends StatefulWidget {
  final List<String> items;
  
  const SearchableList({Key? key, required this.items}) : super(key: key);
  
  @override
  _SearchableListState createState() => _SearchableListState();
}

class _SearchableListState extends State<SearchableList> {
  final _searchController = TextEditingController();
  List<String> _filteredItems = [];
  
  @override
  void initState() {
    super.initState();
    _filteredItems = widget.items;
    _searchController.addListener(_filterItems);
  }
  
  void _filterItems() {
    final query = _searchController.text.toLowerCase();
    setState(() {
      _filteredItems = widget.items
          .where((item) => item.toLowerCase().contains(query))
          .toList();
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: EdgeInsets.all(AppSpacing.md),
          child: AppTextField(
            controller: _searchController,
            hintText: '검색어를 입력하세요',
            labelText: '검색',
          ),
        ),
        Expanded(
          child: ListView.builder(
            itemCount: _filteredItems.length,
            itemBuilder: (context, index) {
              return ListTile(
                title: Text(_filteredItems[index], style: AppTextStyles.body),
                onTap: () => _onItemTap(_filteredItems[index]),
              );
            },
          ),
        ),
      ],
    );
  }
  
  void _onItemTap(String item) {
    // 아이템 선택 로직
  }
}
```

### 3. 결과 테이블/데이터 그리드
```dart
class DataTable extends StatelessWidget {
  final List<Map<String, dynamic>> data;
  final List<String> columns;
  
  const DataTable({
    Key? key,
    required this.data,
    required this.columns,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        headingRowColor: MaterialStateColor.resolveWith(
          (states) => AppColors.surface,
        ),
        columns: columns.map((column) {
          return DataColumn(
            label: Text(
              column,
              style: AppTextStyles.heading2,
            ),
          );
        }).toList(),
        rows: data.map((row) {
          return DataRow(
            cells: columns.map((column) {
              return DataCell(
                Text(
                  row[column]?.toString() ?? '',
                  style: AppTextStyles.body,
                ),
              );
            }).toList(),
          );
        }).toList(),
      ),
    );
  }
}
```

---

## 🚀 성능 최적화

### 1. 이미지 최적화
```dart
// 캐시된 네트워크 이미지
CachedNetworkImage(
  imageUrl: imageUrl,
  placeholder: (context, url) => AppLoading(),
  errorWidget: (context, url, error) => Icon(Icons.error),
  fit: BoxFit.cover,
)
```

### 2. 리스트 성능 최적화
```dart
// 큰 리스트의 경우
ListView.builder(
  itemCount: items.length,
  cacheExtent: 500, // 미리 렌더링할 범위
  itemBuilder: (context, index) {
    return _buildOptimizedListItem(items[index]);
  },
)
```

### 3. 상태 관리 최적화
```dart
// Consumer로 필요한 부분만 리빌드
Consumer<AppState>(
  builder: (context, appState, child) {
    return Text(appState.username);
  },
)
```

---

## 📝 체크리스트 요약

### 프로젝트 시작 시 (필수)
- [ ] `AppTheme`, `AppColors`, `AppTextStyles` 클래스 생성
- [ ] `AppButton`, `AppTextField`, `AppLoading` 컴포넌트 생성
- [ ] 상태 관리 라이브러리 설정
- [ ] 라우팅 시스템 구성

### 개발 중간 체크
- [ ] 하드코딩된 색상/스타일 제거
- [ ] 공통 컴포넌트 재사용 확인
- [ ] 반응형 레이아웃 적용
- [ ] 성능 이슈 체크

### 배포 전 최종 체크
- [ ] 디자인 일관성 검토
- [ ] 접근성 테스트
- [ ] 다양한 화면 크기 테스트
- [ ] 성능 프로파일링

---

## 🎯 핵심 원칙

1. **일관성**: 모든 UI 요소가 동일한 디자인 시스템을 따라야 함
2. **재사용성**: 공통 컴포넌트를 만들어 중복 코드 최소화
3. **확장성**: 새로운 기능 추가 시 기존 구조에 맞게 확장
4. **성능**: 불필요한 리빌드와 메모리 사용 최소화
5. **접근성**: 모든 사용자가 사용할 수 있는 인터페이스 구성

**기억하세요**: "지금 30분 투자하면 나중에 몇 시간을 절약할 수 있습니다!" 