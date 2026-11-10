package com.phantomresume.mobile;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import com.google.zxing.*;
import com.google.zxing.common.HybridBinarizer;

public final class NativeSupport {
    public static String decodeQR(byte[] bytes) {
        Bitmap image = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);
        if (image == null) return null;
        try {
            int w=image.getWidth(), h=image.getHeight();
            int[] pixels=new int[w*h]; image.getPixels(pixels,0,w,0,0,w,h);
            return new MultiFormatReader().decode(new BinaryBitmap(new HybridBinarizer(new RGBLuminanceSource(w,h,pixels)))).getText();
        } catch (Exception e) { return null; }
        finally { image.recycle(); }
    }
}
