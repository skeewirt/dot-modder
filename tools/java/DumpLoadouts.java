import java.io.*;
import java.lang.reflect.*;
import java.util.*;
import dot.loading.filecache.FileCache;

public class DumpLoadouts {

  // --- reflection helpers ---
  static Field f(Object o,String n)throws Exception{ Field x=o.getClass().getDeclaredField(n); x.setAccessible(true); return x; }
  static String s(Object o,String n){ try{ Object v=f(o,n).get(o); return v==null? null : String.valueOf(v);}catch(Exception e){ return null; } }
  static Integer i(Object o,String n){ try{ Object v=f(o,n).get(o); if(v==null) return null; if(v instanceof Number) return ((Number)v).intValue(); return Integer.parseInt(String.valueOf(v)); }catch(Exception e){ return null; } }

  static String esc(String t){ if(t==null) return null; StringBuilder b=new StringBuilder(); for(int k=0;k<t.length();k++){ char c=t.charAt(k);
    switch(c){ case '\\': b.append("\\\\"); break; case '"': b.append("\\\""); break; case '\b': b.append("\\b"); break;
      case '\f': b.append("\\f"); break; case '\n': b.append("\\n"); break; case '\r': b.append("\\r"); break; case '\t': b.append("\\t"); break;
      default: if(c<0x20) b.append(String.format("\\u%04x",(int)c)); else b.append(c); } } return b.toString(); }
  static String q(String t){ return t==null? "null" : "\""+esc(t)+"\""; }

  static String csvToJson(String csv){
    if(csv==null || csv.trim().isEmpty()) return "[]";
    String[] parts = csv.split(",");
    StringBuilder sb = new StringBuilder(); sb.append("[");
    int n=0; for(String p:parts){ String v=p.trim(); if(v.isEmpty()) continue; if(n++>0) sb.append(","); sb.append(q(v)); }
    sb.append("]"); return sb.toString();
  }

  static void addKV(StringBuilder out, boolean[] first, String key, String jsonValue){
    if(jsonValue==null) return;
    if(!first[0]) out.append(","); else first[0]=false;
    out.append("\"").append(esc(key)).append("\":").append(jsonValue);
  }

  public static void main(String[] args) throws Exception {
    if(args.length<2){ System.err.println("Usage: java -cp .;<DOT.jar> DumpLoadouts <modules\\loadouts.dat> <arrays:true|false>"); System.exit(1); }
    String dat = args[0];
    boolean arrays = Boolean.parseBoolean(args[1]);

    Object root = new ObjectInputStream(new FileInputStream(dat)).readObject();
    FileCache fc = (FileCache) root;

    Object loadoutsXml = fc.xmlFiles.get("/modules/loadouts/data/loadouts.xml");
    if(loadoutsXml==null){
      for(Object k : fc.xmlFiles.keySet()){
        if(k instanceof String && ((String)k).toLowerCase().endsWith("loadouts.xml")) { loadoutsXml = fc.xmlFiles.get(k); break; }
      }
    }
    if(loadoutsXml==null){ System.out.print("[]"); return; }

    Object arrObj = f(loadoutsXml,"loadouts").get(loadoutsXml);
    if(!(arrObj instanceof Object[])){ System.out.print("[]"); return; }
    Object[] arr = (Object[]) arrObj;

    StringBuilder out=new StringBuilder(); out.append("[");
    for(int idx=0; idx<arr.length; idx++){
      Object L = arr[idx];
      if(idx>0) out.append(",");
      out.append("{");

      String key         = s(L,"key");
      String name        = s(L,"name");
      String description = s(L,"description");
      Integer sortOrder  = i(L,"sortOrder");
      Integer selMaj     = i(L,"selectMajorSkills");
      Integer selMin     = i(L,"selectMinorSkills");

      String majorSkills = s(L,"majorSkills");
      String minorSkills = s(L,"minorSkills");
      String abilities   = s(L,"abilities");
      String perks       = s(L,"perks");
      String selectPerks = s(L,"selectPerks");

      String lootTable   = s(L,"lootTable");
      String lootDesc    = s(L,"lootDescription");
      String card        = s(L,"card");
      String cardSmall   = s(L,"cardSmall");
      String cardSquare  = s(L,"cardSquare");
      String defaultBody = s(L,"defaultBodyType");
      String warning     = s(L,"warning");

      boolean[] first = new boolean[]{true};
      addKV(out, first, "key", q(key));
      addKV(out, first, "name", q(name));
      addKV(out, first, "description", q(description));
      addKV(out, first, "sortOrder", sortOrder==null? null : String.valueOf(sortOrder));
      addKV(out, first, "selectMajorSkills", selMaj==null? null : String.valueOf(selMaj));
      addKV(out, first, "selectMinorSkills", selMin==null? null : String.valueOf(selMin));

      if(arrays){
        addKV(out, first, "majorSkills", csvToJson(majorSkills));
        addKV(out, first, "minorSkills", csvToJson(minorSkills));
        addKV(out, first, "abilities",   csvToJson(abilities));
        addKV(out, first, "perks",       csvToJson(perks));
        addKV(out, first, "selectPerks", csvToJson(selectPerks));
      }else{
        addKV(out, first, "majorSkills", q(majorSkills));
        addKV(out, first, "minorSkills", q(minorSkills));
        addKV(out, first, "abilities",   q(abilities));
        addKV(out, first, "perks",       q(perks));
        addKV(out, first, "selectPerks", q(selectPerks));
      }

      addKV(out, first, "lootTable",         q(lootTable));
      addKV(out, first, "lootDescription",   q(lootDesc));
      addKV(out, first, "card",              q(card));
      addKV(out, first, "cardSmall",         q(cardSmall));
      addKV(out, first, "cardSquare",        q(cardSquare));
      addKV(out, first, "defaultBodyType",   q(defaultBody));
      addKV(out, first, "warning",           q(warning));

      out.append("}");
    }
    out.append("]");
    System.out.print(out.toString());
  }
}