#pragma once
#include <stdint.h>
namespace LedEffects {
constexpr unsigned Pixels=30;
constexpr int First=15,Last=33;
struct Color { uint8_t r,g,b; };
struct Settings { Color primary{0,184,255},secondary{126,75,255}; unsigned speed=100,width=6; };
inline unsigned lesser(unsigned a,unsigned b){return a<b?a:b;}
inline Color dim(Color c,unsigned v){return {uint8_t(c.r*v/255),uint8_t(c.g*v/255),uint8_t(c.b*v/255)};}
inline Color mix(Color a,Color b,unsigned v){return {uint8_t((a.r*(255-v)+b.r*v)/255),uint8_t((a.g*(255-v)+b.g*v)/255),uint8_t((a.b*(255-v)+b.b*v)/255)};}
inline unsigned triangle(unsigned phase,unsigned half){phase%=half*2;return (phase<half?phase:half*2-1-phase)*255/half;}
inline uint32_t hash(uint32_t x){x^=x>>16;x*=0x7feb352dU;x^=x>>15;x*=0x846ca68bU;return x^(x>>16);}
template<class Strip> void pixel(Strip& s,unsigned i,Color c){s.setPixel(i,c.r,c.g,c.b);}
template<class Strip> void fill(Strip& s,Color c){s.fill(c.r,c.g,c.b);}
// Pure, bounded render: no hardware, sleeps, allocation, random generator or IRQ changes.
template<class Strip> uint32_t render(Strip& s,int mode,uint32_t f,const Settings& cfg=Settings{}){
 s.fill(0,0,0);unsigned delay=50,w=cfg.width;const Color a=cfg.primary,b=cfg.secondary;
 switch(mode){
 case 15:{unsigned head=f%(Pixels/2+w+2);for(unsigned i=0;i<Pixels;++i){unsigned d=i<Pixels/2?Pixels/2-1-i:i-Pixels/2;if(head>=d&&head-d<w)pixel(s,i,dim(a,255-(head-d)*240/w));}delay=60;break;}
 case 16:case 17:{unsigned span=w+5,head=f%span;for(unsigned x=0;x<Pixels;++x){unsigned lag=(head+span-x%span)%span;if(lag<w)pixel(s,mode==16?Pixels-1-x:x,dim(a,255-lag*240/w));}delay=60;break;}
 case 18:{unsigned head=f%Pixels;for(unsigned t=0;t<w;++t)pixel(s,(head+Pixels-t)%Pixels,dim(mix(a,b,t*255/w),255-t*240/w));break;}
 case 19:{unsigned phase=f%3;Color c=mix(a,b,triangle(f/3,16));for(unsigned i=phase;i<Pixels;i+=3)pixel(s,i,c);delay=90;break;}
 case 20:{unsigned p=f%50,v=3;if(p<8)v=(p<4?p+1:8-p)*63;else if(p>=12&&p<20){p-=12;v=(p<4?p+1:8-p)*45;}fill(s,dim(a,v));delay=40;break;}
 case 21:fill(s,dim(a,12+triangle(f,32)*9/10));break;
 case 22:for(unsigned i=0;i<Pixels;++i){unsigned t=triangle(i+f,w*2);pixel(s,i,dim(mix(a,b,t),35+t*220/255));}break;
 case 23:{unsigned period=Pixels+w+3,phase=f%period,origin=hash(f/period)%Pixels;for(unsigned i=0;i<Pixels;++i){unsigned distance=i>origin?i-origin:origin-i;if(phase>=distance&&phase-distance<w)pixel(s,i,dim(mix(a,b,distance*255/Pixels),255-(phase-distance)*240/w));}break;}
 case 24:for(unsigned i=0;i<Pixels;++i){unsigned t=triangle(i*3+f/2,23),v=triangle(i+f,17);pixel(s,i,dim(mix(a,b,t),55+v*200/255));}delay=60;break;
 case 25:for(unsigned i=0;i<Pixels;++i){uint32_t h=hash(i+f/2*977);pixel(s,i,h%30<4?mix(a,b,(h>>8)&255):dim(b,6));}delay=60;break;
 case 26:for(unsigned i=0;i<Pixels;++i){unsigned lag=Pixels;for(unsigned k=0;k<3;++k){unsigned head=(f*(k+1)+k*10)%Pixels;lag=lesser(lag,(head+Pixels-i)%Pixels);}if(lag<w)pixel(s,i,dim(mix(a,b,i*255/Pixels),255-lag*240/w));}break;
 case 27:{unsigned cycle=2*(Pixels-1),p=f%cycle,head=p<Pixels?p:cycle-p;for(unsigned i=0;i<Pixels;++i){unsigned d=i>head?i-head:head-i;if(d<w)pixel(s,i,dim(mix(a,b,head*255/(Pixels-1)),255-d*240/w));}break;}
 case 28:{unsigned p=f%60,count=p<30?p+1:60-p;for(unsigned i=0;i<count;++i)pixel(s,i,mix(a,b,i*255/(Pixels-1)));delay=60;break;}
 case 29:for(unsigned i=0;i<Pixels;++i)pixel(s,i,mix(a,b,triangle(i+f,w*2)));delay=60;break;
 case 30:for(unsigned i=0;i<Pixels;++i){uint32_t h=hash(i*977+42);unsigned t=triangle(f+h%100,20+h%30);pixel(s,i,dim(mix(a,b,(h>>8)&255),t*t/255));}delay=60;break;
 case 31:{unsigned p=f%30,head=p<15?p:29-p;for(unsigned i=0;i<Pixels/2;++i){unsigned d=i>head?i-head:head-i;if(d<w){Color c=dim(mix(a,b,triangle(f,16)),255-d*240/w);pixel(s,i,c);pixel(s,Pixels-1-i,c);}}break;}
 case 32:for(unsigned i=0;i<Pixels;++i){unsigned block=((i+f)/w)%3;if(block<2)pixel(s,i,block?a:b);}delay=60;break;
 case 33:for(unsigned i=0;i<Pixels;++i){uint32_t h=hash(i*41+f/2*97);unsigned t=triangle(i+f/4,w*2);pixel(s,i,dim(mix(a,b,t),80+h%176));}delay=70;break;
 default:delay=100;break;
 }
 const unsigned scaled=delay*100/cfg.speed;return scaled<20?20:scaled>400?400:scaled;
}
}
