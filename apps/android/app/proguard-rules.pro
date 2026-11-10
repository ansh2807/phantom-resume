-keepclassmembers class com.phantomresume.mobile.MainActivity$Bridge {
    @android.webkit.JavascriptInterface <methods>;
}
-keep class com.phantomresume.mobile.NativeSupport { public static *; }
-keep class com.chaquo.python.** { *; }
-dontwarn javax.annotation.**
-keepattributes *Annotation*
