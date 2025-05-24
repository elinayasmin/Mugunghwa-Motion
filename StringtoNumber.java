import java.util.Hashmap;
import java.util.Map;
import java.util.*;

public class StringtoNumber{
    public ststic void main(String args[]){
        Map<String, Integer>wordtoNumber=new HashMap<>();
wordtoNumber.put("Zero",0);
wordtoNumber.put("One",1);
wordtoNumber.put("Two",2);
wordtoNumber.put("Three",3);
wordtoNumber.put("Four",4);
wordtoNumber.put("Five",5);
wordtoNumber.put("Six",6);
wordtoNumber.put("Seven",7);
wordtoNumber.put("Eight",8);
wordtoNumber.put("Nine",9);
wordtoNumber.put("Ten",10);
Scanner sc=new Scanner(System.in);
String input=sc.nextLine();
int num=wordtoNumber.get(input);
if(num !=null){
    System.out.println("Number:"+num);
}else
{
     System.out.println("Invalid");
}
    }
    }
