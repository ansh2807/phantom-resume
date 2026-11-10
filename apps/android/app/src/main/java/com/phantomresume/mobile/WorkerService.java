package com.phantomresume.mobile;

import android.app.Service;
import android.content.Intent;
import android.os.*;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.concurrent.*;

public class WorkerService extends Service {
    private final ExecutorService executor=Executors.newSingleThreadExecutor();
    private boolean busy=false;
    private final Messenger messenger=new Messenger(new Handler(Looper.getMainLooper(), message -> {
        if (message.what==2) { stopSelf(); android.os.Process.killProcess(android.os.Process.myPid()); return true; }
        if (message.what!=1 || busy) return true;
        busy=true;
        String key=message.getData().getString("key"), params=message.getData().getString("params");
        Messenger reply=message.replyTo;
        executor.execute(() -> {
            Message answer=Message.obtain(null,3);
            Bundle bundle=new Bundle();
            try {
                if (!Python.isStarted()) Python.start(new AndroidPlatform(this));
                String result=Python.getInstance().getModule("mobile_api").callAttr("execute",getFilesDir().getAbsolutePath(),key,params).toString();
                File out=new File(getFilesDir(),"worker-result.json");
                Files.write(out.toPath(),result.getBytes(StandardCharsets.UTF_8));
                bundle.putString("result",out.getAbsolutePath());
            } catch (Throwable e) { bundle.putString("error",e.getMessage()==null?e.toString():e.getMessage()); }
            answer.setData(bundle);
            try { reply.send(answer); } catch (RemoteException ignored) {}
        });
        return true;
    }));
    @Override public IBinder onBind(Intent intent) { return messenger.getBinder(); }
    @Override public boolean onUnbind(Intent intent) { stopSelf(); return false; }
    @Override public void onTaskRemoved(Intent rootIntent) { stopSelf(); }
    @Override public void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
        android.os.Process.killProcess(android.os.Process.myPid());
    }
}
