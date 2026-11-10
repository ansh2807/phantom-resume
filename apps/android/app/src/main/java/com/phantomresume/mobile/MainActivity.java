package com.phantomresume.mobile;

import android.app.*;
import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.os.*;
import android.provider.OpenableColumns;
import android.webkit.*;
import android.view.*;
import android.widget.*;
import android.animation.*;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.content.res.ColorStateList;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.graphics.Insets;
import androidx.core.content.FileProvider;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.UUID;
import java.util.concurrent.*;
import java.util.zip.*;

public class MainActivity extends Activity {
    private WebView web;
    private FrameLayout root,splash;
    private Button runAction,cancelAction;
    private AnimatorSet launchMotion;
    private long launchTime;
    private String pendingField="input", pendingKey, pendingParams;
    private File pendingSave;
    private boolean multi=false,bound=false, busy=false;
    private Messenger remote;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final ExecutorService io=Executors.newSingleThreadExecutor();
    private final Runnable timeout=() -> cancel("Stopped after the 15-minute run limit.");
    private final Messenger receiver=new Messenger(new Handler(Looper.getMainLooper(),message -> {
        if (message.what!=3) return false;
        handler.removeCallbacks(timeout);
        String path=message.getData().getString("result");
        String error=message.getData().getString("error");
        final boolean syntheticTest="_selftest".equals(pendingKey);
        releaseWorker(); busy=false;
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        if(error!=null) {if(syntheticTest)android.util.Log.e("PhantomResumeCheck",error);send("failure",JSONObject.quote(error));}
        else io.execute(() -> {
            try {String data=new String(Files.readAllBytes(new File(path).toPath()),StandardCharsets.UTF_8);
                if(syntheticTest){Files.write(new File(getExternalFilesDir(null),"android-selftest.json").toPath(),data.getBytes(StandardCharsets.UTF_8));android.util.Log.i("PhantomResumeCheck",data);}
                send("result",data);}
            catch(Exception e){send("failure",JSONObject.quote(e.toString()));}
        });
        return true;
    }));
    private final ServiceConnection connection=new ServiceConnection(){
        @Override public void onServiceConnected(ComponentName name,IBinder binder){
            remote=new Messenger(binder);
            Message message=Message.obtain(null,1);Bundle data=new Bundle();data.putString("key",pendingKey);data.putString("params",pendingParams);message.setData(data);message.replyTo=receiver;
            try{remote.send(message);}catch(RemoteException e){cancel(e.toString());}
        }
        @Override public void onServiceDisconnected(ComponentName name){if(busy)cancel("The isolated task stopped unexpectedly. Your input is unchanged.");}
    };

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        if(Build.VERSION.SDK_INT>=33)getOnBackInvokedDispatcher().registerOnBackInvokedCallback(0,()->handleBack());
        getWindow().setStatusBarColor(0xff132737);getWindow().setNavigationBarColor(0xff132737);
        web=new WebView(this);
        web.setBackgroundColor(0xfff1f4f7);
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(true);
        web.getSettings().setAllowFileAccessFromFileURLs(false);
        web.getSettings().setAllowUniversalAccessFromFileURLs(false);
        web.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        web.setWebViewClient(new WebViewClient(){
            @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest req){return true;}
            @Override public void onPageFinished(WebView view,String url){
                finishLaunch();
            }
        });
        web.addJavascriptInterface(new Bridge(),"Native");
        root=new FrameLayout(this);root.setBackgroundColor(0xff132737);
        LinearLayout layout=new LinearLayout(this);layout.setOrientation(LinearLayout.VERTICAL);
        root.addView(layout,new FrameLayout.LayoutParams(-1,-1));
        layout.addView(web,new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout bar=new LinearLayout(this);bar.setPadding(dp(16),dp(11),dp(16),dp(12));bar.setBackgroundColor(0xfff1f4f7);bar.setGravity(Gravity.CENTER_VERTICAL);
        runAction=actionButton("Create injected copy",0xff245e48,Color.WHITE);runAction.setOnClickListener(v->web.evaluateJavascript("run()",null));
        bar.addView(runAction,new LinearLayout.LayoutParams(0,dp(54),1));
        cancelAction=actionButton("Cancel",0xffffeedf,0xff86562b);cancelAction.setOnClickListener(v->cancel("Cancelled. Partial exports remain marked INCOMPLETE."));
        LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(dp(84),dp(54));cp.leftMargin=dp(9);bar.addView(cancelAction,cp);cancelAction.setVisibility(View.GONE);layout.addView(bar,new LinearLayout.LayoutParams(-1,-2));
        ViewCompat.setOnApplyWindowInsetsListener(root,(view,insets)->{
            Insets bars=insets.getInsets(WindowInsetsCompat.Type.systemBars()|WindowInsetsCompat.Type.displayCutout()|WindowInsetsCompat.Type.ime());
            view.setPadding(bars.left,bars.top,bars.right,bars.bottom);return insets;
        });
        setContentView(root);ViewCompat.requestApplyInsets(root);showLaunch();
        web.loadUrl("file:///android_asset/index.html");
        if(getIntent().getBooleanExtra("selftest",false)){
            getIntent().removeExtra("selftest");handler.postDelayed(()->runJob("_selftest","{}"),1000);
        }
    }
    private int dp(float n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private Button actionButton(String text,int background,int foreground){
        Button button=new Button(this);button.setText(text);button.setTextSize(14);button.setAllCaps(false);button.setTextColor(foreground);button.setPadding(dp(8),0,dp(8),0);
        GradientDrawable shape=new GradientDrawable();shape.setColor(background);shape.setCornerRadius(dp(14));button.setBackground(new RippleDrawable(ColorStateList.valueOf(0x22ffffff),shape,null));return button;
    }
    private void showLaunch(){
        launchTime=SystemClock.uptimeMillis();
        splash=new FrameLayout(this);splash.setBackgroundColor(0xff132737);root.addView(splash,new FrameLayout.LayoutParams(-1,-1));
        LinearLayout center=new LinearLayout(this);center.setOrientation(LinearLayout.VERTICAL);center.setGravity(Gravity.CENTER);
        FrameLayout.LayoutParams position=new FrameLayout.LayoutParams(-1,-2,Gravity.CENTER);splash.addView(center,position);
        ImageView logo=new ImageView(this);logo.setImageResource(R.drawable.phantom);center.addView(logo,new LinearLayout.LayoutParams(dp(100),dp(100)));
        TextView name=new TextView(this);name.setText("PhantomResume");name.setTextSize(28);name.setGravity(Gravity.CENTER);name.setTextColor(Color.WHITE);name.setTypeface(null,1);name.setPadding(0,dp(25),0,dp(8));center.addView(name);
        TextView note=new TextView(this);note.setText("Your documents. Your possibilities.");note.setTextSize(14);note.setGravity(Gravity.CENTER);note.setTextColor(0xffb9d4d3);center.addView(note);
        TextView foot=new TextView(this);foot.setText("Made for your next chapter");foot.setTextSize(12);foot.setTextColor(0xff8cafb8);foot.setGravity(Gravity.CENTER);FrameLayout.LayoutParams fp=new FrameLayout.LayoutParams(-1,dp(50),Gravity.BOTTOM);fp.bottomMargin=dp(24);splash.addView(foot,fp);
        if(ValueAnimator.areAnimatorsEnabled()){
            launchMotion=new AnimatorSet();launchMotion.playTogether(ObjectAnimator.ofFloat(logo,"translationY",dp(18),dp(-5),0),ObjectAnimator.ofFloat(logo,"scaleX",.82f,1.05f,1f),ObjectAnimator.ofFloat(logo,"scaleY",.82f,1.05f,1f),ObjectAnimator.ofFloat(center,"alpha",0f,1f));launchMotion.setDuration(800);launchMotion.start();
        }
    }
    private void finishLaunch(){
        long delay=ValueAnimator.areAnimatorsEnabled()?Math.max(0,900-(SystemClock.uptimeMillis()-launchTime)):0;
        handler.postDelayed(()->{if(splash==null)return;FrameLayout old=splash;splash=null;
            if(ValueAnimator.areAnimatorsEnabled())old.animate().alpha(0).setDuration(220).withEndAction(()->root.removeView(old)).start();else root.removeView(old);
        },delay);
    }
    private void send(String type,String payload){handler.post(()->{if(web!=null)web.evaluateJavascript("window.receive("+JSONObject.quote(type)+","+payload+")",null);});}
    private void runJob(String key,String params){
        if(busy){send("failure",JSONObject.quote("One task is already running."));return;}
        busy=true;pendingKey=key;pendingParams=params;
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        send("progress",JSONObject.quote("Starting isolated task…"));
        bound=bindService(new Intent(this,WorkerService.class),connection,Context.BIND_AUTO_CREATE);
        if(!bound){busy=false;getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);send("failure",JSONObject.quote("Could not start task process."));}
        else handler.postDelayed(timeout,15*60*1000);
    }
    private void releaseWorker(){
        handler.removeCallbacks(timeout);
        if(bound){try{unbindService(connection);}catch(Exception ignored){}bound=false;}
        stopService(new Intent(this,WorkerService.class));remote=null;
    }
    private void cancel(String reason){
        if(remote!=null)try{remote.send(Message.obtain(null,2));}catch(Exception ignored){}
        releaseWorker();busy=false;send("failure",JSONObject.quote(reason));
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    }
    public class Bridge {
        @JavascriptInterface public void setAction(String title,boolean active){handler.post(()->{runAction.setText(title);runAction.setEnabled(!active);runAction.setAlpha(active?.6f:1f);cancelAction.setVisibility(active?View.VISIBLE:View.GONE);});}
        @JavascriptInterface public void run(String key,String params){handler.post(()->runJob(key,params));}
        @JavascriptInterface public void cancel(){handler.post(()->MainActivity.this.cancel("Cancelled. Partial exports are marked INCOMPLETE; originals are unchanged."));}
        @JavascriptInterface public void close(){handler.post(()->{MainActivity.this.cancel("Closed");finishAndRemoveTask();});}
        @JavascriptInterface public void pick(String key,boolean multiple){handler.post(()->{
            if(busy)return;pendingField=key;multi=multiple;
            Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("*/*");i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,multiple);startActivityForResult(i,41);
        });}
        @JavascriptInterface public void save(String path){handler.post(()->{
            try{pendingSave=ownedExport(path);Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType(mime(pendingSave));i.putExtra(Intent.EXTRA_TITLE,pendingSave.getName());startActivityForResult(i,42);}catch(Exception e){send("failure",JSONObject.quote(e.getMessage()));}
        });}
        @JavascriptInterface public void share(String path){handler.post(()->{
            try{File f=ownedExport(path);Uri uri=FileProvider.getUriForFile(MainActivity.this,getPackageName()+".files",f);Intent i=new Intent(Intent.ACTION_SEND).setType(mime(f));i.putExtra(Intent.EXTRA_STREAM,uri);i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);startActivity(Intent.createChooser(i,"Share exported file"));}catch(Exception e){send("failure",JSONObject.quote(e.getMessage()));}
        });}
        @JavascriptInterface public void exportZip(String directory){io.execute(()->{
            try{File dir=new File(directory).getCanonicalFile();File exports=new File(getFilesDir(),"exports").getCanonicalFile();if(!dir.getPath().startsWith(exports.getPath()+File.separator))throw new IOException("Invalid export folder");File zip=new File(exports,"run-"+UUID.randomUUID().toString().substring(0,8)+".zip");try(ZipOutputStream z=new ZipOutputStream(new FileOutputStream(zip))){pack(dir,dir,z);}handler.post(()->save(zip.getAbsolutePath()));}catch(Exception e){send("failure",JSONObject.quote(e.toString()));}
        });}
    }
    private static void copy(InputStream in, OutputStream out) throws IOException { byte[] buffer=new byte[65536];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n); }
    private void pack(File base,File dir,ZipOutputStream out)throws IOException{
        File[] files=dir.listFiles();if(files==null)return;
        for(File file:files){if(file.isDirectory())pack(base,file,out);else{out.putNextEntry(new ZipEntry(base.toPath().relativize(file.toPath()).toString().replace('\\','/')));try(InputStream input=new FileInputStream(file)){copy(input,out);}out.closeEntry();}}
    }
    private File ownedExport(String path)throws IOException{
        File f=new File(path).getCanonicalFile(), root=new File(getFilesDir(),"exports").getCanonicalFile();
        if(!f.isFile()||!f.getPath().startsWith(root.getPath()+File.separator))throw new IOException("Select an existing exported file.");return f;
    }
    private String mime(File f){String n=f.getName().toLowerCase();return n.endsWith(".pdf")?"application/pdf":n.endsWith(".docx")?"application/vnd.openxmlformats-officedocument.wordprocessingml.document":n.endsWith(".zip")?"application/zip":n.endsWith(".png")?"image/png":"text/plain";}
    private File importFile(Uri uri,File directory)throws IOException{
        String name="document";try(Cursor cursor=getContentResolver().query(uri,null,null,null,null)){if(cursor!=null&&cursor.moveToFirst())name=cursor.getString(cursor.getColumnIndexOrThrow(OpenableColumns.DISPLAY_NAME));}
        name=new File(name).getName().replaceAll("[^\\p{L}\\p{N} ._()-]","_");directory.mkdirs();File out=new File(directory,name);
        try(InputStream input=getContentResolver().openInputStream(uri);OutputStream output=new FileOutputStream(out)){
            byte[] buffer=new byte[65536];long count=0;int n;while((n=input.read(buffer))!=-1){count+=n;if(count>128L*1024*1024)throw new IOException("File exceeds 128 MB.");output.write(buffer,0,n);}
        }return out;
    }
    @Override protected void onActivityResult(int request,int result,Intent intent){
        super.onActivityResult(request,result,intent);if(result!=RESULT_OK||intent==null)return;
        if(request==41){String field=pendingField;boolean multiple=multi;io.execute(()->{
            try{File directory=new File(getFilesDir(),"imports/"+UUID.randomUUID());File first=null;
                if(intent.getClipData()!=null){for(int i=0;i<intent.getClipData().getItemCount();i++){File f=importFile(intent.getClipData().getItemAt(i).getUri(),directory);if(first==null)first=f;}}
                else first=importFile(intent.getData(),directory);
                JSONObject data=new JSONObject();data.put("key",field);data.put("path",multiple?directory.getAbsolutePath():first.getAbsolutePath());data.put("name",multiple?"Selected DOCX files":first.getName());send("file",data.toString());
            }catch(Exception e){send("failure",JSONObject.quote(e.toString()));}
        });}
        if(request==42){File file=pendingSave;Uri uri=intent.getData();io.execute(()->{
            try(InputStream in=new FileInputStream(file);OutputStream out=getContentResolver().openOutputStream(uri)){copy(in,out);send("notice",JSONObject.quote("Saved to your selected location."));}catch(Exception e){send("failure",JSONObject.quote(e.toString()));}
        });}
    }
    @Override protected void onPause(){if(web!=null){web.evaluateJavascript("document.body.classList.add('paused')",null);web.onPause();}super.onPause();}
    @Override protected void onResume(){super.onResume();if(web!=null){web.onResume();web.evaluateJavascript("document.body.classList.remove('paused')",null);}}
    private void handleBack(){
        if(web==null){requestClose();return;}
        web.evaluateJavascript("(()=>{if(document.getElementById('drawer')?.classList.contains('open')){drawer(false);return true}return false})()",value->{if(!"true".equals(value))requestClose();});
    }
    private void requestClose(){if(busy){new AlertDialog.Builder(this).setTitle("Close PhantomResume?").setMessage("The running task will stop. Original files stay unchanged.").setPositiveButton("Close",(d,w)->{cancel("Closed");finishAndRemoveTask();}).setNegativeButton("Stay",null).show();}else finishAndRemoveTask();}
    @Override public void onBackPressed(){handleBack();}
    @Override protected void onDestroy(){
        boolean explicitExit=isFinishing();releaseWorker();if(launchMotion!=null)launchMotion.cancel();handler.removeCallbacksAndMessages(null);io.shutdownNow();
        if(web!=null){web.removeJavascriptInterface("Native");web.stopLoading();web.destroy();web=null;}super.onDestroy();
        // Explicit exit releases this app's cached WebView bindings as well as its
        // worker. Home/backgrounding does not execute this exit path.
        if(explicitExit)new Handler(Looper.getMainLooper()).postDelayed(()->android.os.Process.killProcess(android.os.Process.myPid()),150);
    }
}
