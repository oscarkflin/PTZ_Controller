package com.oscarkflin.ptz;

import android.content.Context;
import android.graphics.*;
import android.view.*;

/** Captures one finger and reports normalized displacement; releases to zero. */
public final class JoystickView extends View {
    public interface Listener { void onMove(float x, float y); }
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Listener listener;
    private float x, y;
    private int pointer = -1;
    public JoystickView(Context context, Listener listener) {
        super(context); this.listener=listener;
        setContentDescription("Pan and tilt joystick. Drag from center to move; release to stop.");
    }
    private float radius(){return Math.min(getWidth(),getHeight())*.39f;}
    @Override protected void onDraw(Canvas c){
        super.onDraw(c); float cx=getWidth()/2f,cy=getHeight()/2f,r=radius();
        paint.setStyle(Paint.Style.FILL);paint.setColor(Color.rgb(17,32,49));c.drawCircle(cx,cy,r,paint);
        paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(2);paint.setColor(Color.rgb(44,68,93));
        c.drawCircle(cx,cy,r,paint);c.drawCircle(cx,cy,r*.60f,paint);
        c.drawLine(cx-r,cy,cx+r,cy,paint);c.drawLine(cx,cy-r,cx,cy+r,paint);
        paint.setStyle(Paint.Style.FILL);paint.setColor(Color.rgb(49,135,220));
        c.drawCircle(cx+x*r,cy-y*r,r*.30f,paint);
        paint.setColor(Color.rgb(119,198,255));c.drawCircle(cx+x*r,cy-y*r,r*.13f,paint);
        paint.setTextAlign(Paint.Align.CENTER);paint.setTextSize(13*getResources().getDisplayMetrics().scaledDensity);
        paint.setColor(Color.rgb(139,164,189));c.drawText("PAN / TILT",cx,cy+r+28,paint);
    }
    @Override public boolean onTouchEvent(MotionEvent e){
        int action=e.getActionMasked();
        if(action==MotionEvent.ACTION_DOWN){pointer=e.getPointerId(0);getParent().requestDisallowInterceptTouchEvent(true);}
        if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_CANCEL||
            (action==MotionEvent.ACTION_POINTER_UP&&e.getPointerId(e.getActionIndex())==pointer)){
            release();getParent().requestDisallowInterceptTouchEvent(false);performClick();return true;
        }
        int index=e.findPointerIndex(pointer);if(index<0)return true;
        x=(e.getX(index)-getWidth()/2f)/radius();y=-(e.getY(index)-getHeight()/2f)/radius();
        float length=(float)Math.sqrt(x*x+y*y);if(length>1){x/=length;y/=length;}
        listener.onMove(x,y);invalidate();return true;
    }
    public void release(){pointer=-1;x=y=0;listener.onMove(0,0);invalidate();}
    @Override public boolean performClick(){super.performClick();return true;}
}
