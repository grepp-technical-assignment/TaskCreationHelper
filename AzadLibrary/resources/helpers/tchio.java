import java.io.FileWriter;
import java.io.IOException;
import java.util.Scanner;

public class tchio {

    // 0 dimensional primitive input
    public static int get0dint(Scanner sc){
        return sc.nextInt();
    }
    public static long get0dlong(Scanner sc){
        return sc.nextLong();
    }
    public static float get0dfloat(Scanner sc){
        return sc.nextFloat();
    }
    public static double get0ddouble(Scanner sc){
        return sc.nextDouble();
    }
    public static boolean get0dboolean(Scanner sc){
        return sc.next() == "true";
    }
    public static String get0dString(Scanner sc){
        int len = get0dint(sc);
        char[] charArray = new char[len];
        for(int i=0; i<len; i++) charArray[i] = (char)get0dint(sc);
        return new String(charArray);
    }

    // 1 dimensional primitive input
    public static int[] get1dint(Scanner sc){
        int len = get0dint(sc);
        int[] result = new int[len];
        for(int i=0; i<len; i++) result[i] = get0dint(sc);
        return result;
    }
    public static long[] get1dlong(Scanner sc){
        int len = get0dint(sc);
        long[] result = new long[len];
        for(int i=0; i<len; i++) result[i] = get0dlong(sc);
        return result;
    }
    public static float[] get1dfloat(Scanner sc){
        int len = get0dint(sc);
        float[] result = new float[len];
        for(int i=0; i<len; i++) result[i] = get0dfloat(sc);
        return result;
    }
    public static double[] get1ddouble(Scanner sc){
        int len = get0dint(sc);
        double[] result = new double[len];
        for(int i=0; i<len; i++) result[i] = get0ddouble(sc);
        return result;
    }
    public static boolean[] get1dboolean(Scanner sc){
        int len = get0dint(sc);
        boolean[] result = new boolean[len];
        for(int i=0; i<len; i++) result[i] = get0dboolean(sc);
        return result;
    }
    public static String[] get1dString(Scanner sc){
        int len = get0dint(sc);
        String[] result = new String[len];
        for(int i=0; i<len; i++) result[i] = get0dString(sc);
        return result;
    }

    // 2+ dimensional primitive input
    public static int[][] get2dint(Scanner sc){
        int len = get0dint(sc);
        int[][] result = new int[len][];
        for(int i=0; i<len; i++) result[i] = get1dint(sc);
        return result;
    }
    public static long[][] get2dlong(Scanner sc){
        int len = get0dint(sc);
        long[][] result = new long[len][];
        for(int i=0; i<len; i++) result[i] = get1dlong(sc);
        return result;
    }
    public static float[][] get2dfloat(Scanner sc){
        int len = get0dint(sc);
        float[][] result = new float[len][];
        for(int i=0; i<len; i++) result[i] = get1dfloat(sc);
        return result;
    }
    public static double[][] get2ddouble(Scanner sc){
        int len = get0dint(sc);
        double[][] result = new double[len][];
        for(int i=0; i<len; i++) result[i] = get1ddouble(sc);
        return result;
    }
    public static boolean[][] get2dboolean(Scanner sc){
        int len = get0dint(sc);
        boolean[][] result = new boolean[len][];
        for(int i=0; i<len; i++) result[i] = get1dboolean(sc);
        return result;
    }
    public static String[][] get2dString(Scanner sc){
        int len = get0dint(sc);
        String[][] result = new String[len][];
        for(int i=0; i<len; i++) result[i] = get1dString(sc);
        return result;
    }

    // 0 dimensional primitive output
    public static void put(FileWriter fw, int v) throws IOException{
        fw.write(Integer.toString(v) + "\n");
    }
    public static void put(FileWriter fw, long v) throws IOException{
        fw.write(Long.toString(v) + "\n");
    }
    public static void put(FileWriter fw, float v) throws IOException{
        fw.write(Float.toString(v) + "\n");
    }
    public static void put(FileWriter fw, double v) throws IOException{
        fw.write(Double.toString(v) + "\n");
    }
    public static void put(FileWriter fw, boolean v) throws IOException{
        fw.write(Boolean.toString(v) + "\n");
    }
    public static void put(FileWriter fw, String v) throws IOException{
        int len = v.length(); put(fw, len);
        for(int i=0; i<len; i++) put(fw, (int)v.charAt(i));
    }

    // 1 dimensional primitive output
    public static void put(FileWriter fw, int[] v) throws IOException{
        put(fw, v.length);
        for(int i=0; i<v.length; i++) put(fw, v[i]);
    }
    public static void put(FileWriter fw, long[] v) throws IOException{
        put(fw, v.length);
        for(int i=0; i<v.length; i++) put(fw, v[i]);
    }
    public static void put(FileWriter fw, float[] v) throws IOException{
        put(fw, v.length);
        for(int i=0; i<v.length; i++) put(fw, v[i]);
    }
    public static void put(FileWriter fw, double[] v) throws IOException{
        put(fw, v.length);
        for(int i=0; i<v.length; i++) put(fw, v[i]);
    }
    public static void put(FileWriter fw, boolean[] v) throws IOException{
        put(fw, v.length);
        for(int i=0; i<v.length; i++) put(fw, v[i]);
    }
    public static void put(FileWriter fw, String[] v) throws IOException{
        put(fw, v.length);
        for(int i=0; i<v.length; i++) put(fw, v[i]);
    }

    // 2 dimensional primitive output
    public static void put(FileWriter fw, int[][] v) throws IOException{
        put(fw, v.length);
        for(int i=0; i<v.length; i++) put(fw, v[i]);
    }
    public static void put(FileWriter fw, long[][] v) throws IOException{
        put(fw, v.length);
        for(int i=0; i<v.length; i++) put(fw, v[i]);
    }
    public static void put(FileWriter fw, float[][] v) throws IOException{
        put(fw, v.length);
        for(int i=0; i<v.length; i++) put(fw, v[i]);
    }
    public static void put(FileWriter fw, double[][] v) throws IOException{
        put(fw, v.length);
        for(int i=0; i<v.length; i++) put(fw, v[i]);
    }
    public static void put(FileWriter fw, boolean[][] v) throws IOException{
        put(fw, v.length);
        for(int i=0; i<v.length; i++) put(fw, v[i]);
    }
    public static void put(FileWriter fw, String[][] v) throws IOException{
        put(fw, v.length);
        for(int i=0; i<v.length; i++) put(fw, v[i]);
    }
}

