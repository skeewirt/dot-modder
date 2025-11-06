import java.io.*;
import java.lang.reflect.*;
import java.util.*;
import dot.loading.filecache.FileCache;

public class WriteLoadouts {

  // --- reflection helpers (shared with DumpLoadouts) ---
  static Field f(Object o, String n) throws Exception {
    Field x = o.getClass().getDeclaredField(n);
    x.setAccessible(true);
    return x;
  }

  static void set(Object o, String field, Object value) throws Exception {
    Field x = f(o, field);
    x.set(o, value);
  }

  static String s(Object o, String n) {
    try {
      Object v = f(o, n).get(o);
      return v == null ? null : String.valueOf(v);
    } catch (Exception e) {
      return null;
    }
  }

  static class JsonParseException extends RuntimeException {
    JsonParseException(String msg) { super(msg); }
  }

  static class JsonParser {
    private final String text;
    private int pos;

    JsonParser(String text) {
      this.text = text;
      this.pos = 0;
    }

    static Object parse(String text) {
      return new JsonParser(text).parseValue();
    }

    private void skipWs() {
      while (pos < text.length()) {
        char c = text.charAt(pos);
        if (c == ' ' || c == '\n' || c == '\r' || c == '\t') {
          pos++;
        } else {
          break;
        }
      }
    }

    private char peek() {
      if (pos >= text.length()) {
        return '\0';
      }
      return text.charAt(pos);
    }

    private char next() {
      if (pos >= text.length()) {
        return '\0';
      }
      return text.charAt(pos++);
    }

    private Object parseValue() {
      skipWs();
      char c = peek();
      switch (c) {
        case '{':
          return parseObject();
        case '[':
          return parseArray();
        case '"':
          return parseString();
        case 't':
          expect("true");
          return Boolean.TRUE;
        case 'f':
          expect("false");
          return Boolean.FALSE;
        case 'n':
          expect("null");
          return null;
        default:
          if (c == '-' || (c >= '0' && c <= '9')) {
            return parseNumber();
          }
      }
      throw new JsonParseException("Unexpected value at position " + pos);
    }

    private void expect(String token) {
      for (int i = 0; i < token.length(); i++) {
        if (next() != token.charAt(i)) {
          throw new JsonParseException("Expected token " + token);
        }
      }
    }

    private Number parseNumber() {
      int start = pos;
      if (peek() == '-') {
        pos++;
      }
      while (pos < text.length() && Character.isDigit(text.charAt(pos))) {
        pos++;
      }
      if (pos < text.length() && text.charAt(pos) == '.') {
        pos++;
        while (pos < text.length() && Character.isDigit(text.charAt(pos))) {
          pos++;
        }
      }
      String num = text.substring(start, pos);
      if (num.indexOf('.') >= 0) {
        return Double.parseDouble(num);
      }
      return Long.parseLong(num);
    }

    private String parseString() {
      if (next() != '"') {
        throw new JsonParseException("Expected string");
      }
      StringBuilder sb = new StringBuilder();
      while (true) {
        if (pos >= text.length()) {
          throw new JsonParseException("Unterminated string");
        }
        char c = next();
        if (c == '"') {
          break;
        }
        if (c == '\\') {
          if (pos >= text.length()) {
            throw new JsonParseException("Bad escape");
          }
          char esc = next();
          switch (esc) {
            case '"': sb.append('"'); break;
            case '\\': sb.append('\\'); break;
            case '/': sb.append('/'); break;
            case 'b': sb.append('\b'); break;
            case 'f': sb.append('\f'); break;
            case 'n': sb.append('\n'); break;
            case 'r': sb.append('\r'); break;
            case 't': sb.append('\t'); break;
            case 'u':
              if (pos + 4 > text.length()) {
                throw new JsonParseException("Bad unicode escape");
              }
              String hex = text.substring(pos, pos + 4);
              sb.append((char) Integer.parseInt(hex, 16));
              pos += 4;
              break;
            default:
              throw new JsonParseException("Unsupported escape: \\" + esc);
          }
        } else {
          sb.append(c);
        }
      }
      return sb.toString();
    }

    private Map<String, Object> parseObject() {
      if (next() != '{') {
        throw new JsonParseException("Expected object");
      }
      Map<String, Object> out = new LinkedHashMap<>();
      skipWs();
      if (peek() == '}') {
        next();
        return out;
      }
      while (true) {
        skipWs();
        String key = parseString();
        skipWs();
        if (next() != ':') {
          throw new JsonParseException("Expected ':' after key");
        }
        Object val = parseValue();
        out.put(key, val);
        skipWs();
        char c = next();
        if (c == '}') {
          break;
        }
        if (c != ',') {
          throw new JsonParseException("Expected ',' in object");
        }
      }
      return out;
    }

    private List<Object> parseArray() {
      if (next() != '[') {
        throw new JsonParseException("Expected array");
      }
      List<Object> out = new ArrayList<>();
      skipWs();
      if (peek() == ']') {
        next();
        return out;
      }
      while (true) {
        Object val = parseValue();
        out.add(val);
        skipWs();
        char c = next();
        if (c == ']') {
          break;
        }
        if (c != ',') {
          throw new JsonParseException("Expected ',' in array");
        }
      }
      return out;
    }
  }

  static String listToCsv(Object arrVal) {
    if (arrVal == null) return null;
    if (!(arrVal instanceof List)) return String.valueOf(arrVal);
    @SuppressWarnings("unchecked")
    List<Object> list = (List<Object>) arrVal;
    StringBuilder sb = new StringBuilder();
    for (Object item : list) {
      if (item == null) continue;
      String text = String.valueOf(item).trim();
      if (text.isEmpty()) continue;
      if (sb.length() > 0) sb.append(", ");
      sb.append(text);
    }
    return sb.length() == 0 ? "" : sb.toString();
  }

  static Integer toInt(Object v) {
    if (v == null) return null;
    if (v instanceof Number) return ((Number) v).intValue();
    String s = String.valueOf(v).trim();
    if (s.isEmpty()) return null;
    return Integer.parseInt(s);
  }

  static void applyRecord(Object target, Map<String, Object> record) throws Exception {
    set(target, "key", record.get("key"));
    set(target, "name", record.get("name"));
    set(target, "description", record.get("description"));
    set(target, "warning", record.get("warning"));
    set(target, "lootTable", record.get("lootTable"));
    set(target, "lootDescription", record.get("lootDescription"));
    set(target, "card", record.get("card"));
    set(target, "cardSmall", record.get("cardSmall"));
    set(target, "cardSquare", record.get("cardSquare"));
    set(target, "defaultBodyType", record.get("defaultBodyType"));

    Field sortField = f(target, "sortOrder");
    if (sortField.getType() == int.class) {
      Integer v = toInt(record.get("sortOrder"));
      sortField.setInt(target, v == null ? 0 : v);
    } else {
      sortField.set(target, toInt(record.get("sortOrder")));
    }

    Field majorField = f(target, "selectMajorSkills");
    if (majorField.getType() == int.class) {
      Integer v = toInt(record.get("selectMajorSkills"));
      majorField.setInt(target, v == null ? 0 : v);
    } else {
      majorField.set(target, toInt(record.get("selectMajorSkills")));
    }

    Field minorField = f(target, "selectMinorSkills");
    if (minorField.getType() == int.class) {
      Integer v = toInt(record.get("selectMinorSkills"));
      minorField.setInt(target, v == null ? 0 : v);
    } else {
      minorField.set(target, toInt(record.get("selectMinorSkills")));
    }

    set(target, "majorSkills", listToCsv(record.get("majorSkills")));
    set(target, "minorSkills", listToCsv(record.get("minorSkills")));
    set(target, "abilities", listToCsv(record.get("abilities")));
    set(target, "perks", listToCsv(record.get("perks")));
    set(target, "selectPerks", listToCsv(record.get("selectPerks")));
  }

  @SuppressWarnings("unchecked")
  public static void main(String[] args) throws Exception {
    if (args.length < 2) {
      System.err.println("Usage: java -cp .;<DOT.jar> WriteLoadouts <modules\\loadouts.dat> <json file>");
      System.exit(1);
    }
    String datPath = args[0];
    String jsonPath = args[1];

    StringBuilder buf = new StringBuilder();
    try (BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(jsonPath), "UTF-8"))) {
      String line;
      while ((line = br.readLine()) != null) {
        buf.append(line);
      }
    }

    Object parsed = JsonParser.parse(buf.toString());
    if (!(parsed instanceof List)) {
      throw new JsonParseException("Expected top-level array");
    }
    List<Object> records = (List<Object>) parsed;

    ObjectInputStream ois = new ObjectInputStream(new FileInputStream(datPath));
    Object root = ois.readObject();
    ois.close();
    FileCache fc = (FileCache) root;

    Object loadoutsXml = fc.xmlFiles.get("/modules/loadouts/data/loadouts.xml");
    if (loadoutsXml == null) {
      for (Object k : fc.xmlFiles.keySet()) {
        if (k instanceof String && ((String) k).toLowerCase().endsWith("loadouts.xml")) {
          loadoutsXml = fc.xmlFiles.get(k);
          break;
        }
      }
    }
    if (loadoutsXml == null) {
      throw new IllegalStateException("loadouts.xml not found in cache");
    }

    Field loadoutsField = f(loadoutsXml, "loadouts");
    Object arrObj = loadoutsField.get(loadoutsXml);
    if (!(arrObj instanceof Object[])) {
      throw new IllegalStateException("Unexpected loadouts holder");
    }

    Object[] arr = (Object[]) arrObj;
    Class<?> component = arr.getClass().getComponentType();
    Map<String, Object> existing = new HashMap<>();
    for (Object obj : arr) {
      String key = s(obj, "key");
      if (key != null) {
        existing.put(key, obj);
      }
    }

    List<Object> newList = new ArrayList<>();
    for (Object recObj : records) {
      if (!(recObj instanceof Map)) {
        continue;
      }
      Map<String, Object> rec = (Map<String, Object>) recObj;
      Object keyObj = rec.get("key");
      if (keyObj == null) {
        continue;
      }
      String key = String.valueOf(keyObj);
      Object target = existing.containsKey(key) ? existing.get(key) : component.getDeclaredConstructor().newInstance();
      applyRecord(target, rec);
      newList.add(target);
    }

    Object[] newArr = (Object[]) java.lang.reflect.Array.newInstance(component, newList.size());
    for (int i = 0; i < newList.size(); i++) {
      newArr[i] = newList.get(i);
    }
    loadoutsField.set(loadoutsXml, newArr);

    ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(datPath));
    oos.writeObject(fc);
    oos.close();
  }
}
